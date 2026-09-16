import { useState, useRef, useEffect } from 'react'

import VideoBackground from '../components/VideoBackground'
import { randomGuestNames } from '../guestNames'
import { RFID_API_URL } from '../config'

/** Strip CR/LF and surrounding whitespace from keyboard-wedge scans. */
function normalizeCardId(raw) {
  return String(raw ?? '').replace(/[\r\n]/g, '').trim()
}

function validationError(data) {
  if (data.reason === 'insufficient_time') {
    return `Not enough time (${data.minutes_remaining} min left). Need at least 5 min.`
  }
  if (data.reason === 'expired') return 'Session expired. Visit reception.'
  if (data.reason === 'no_active_session') return 'No active session. Visit reception.'
  return 'Card not recognized.'
}

async function validateRfidCard(cardId) {
  const res = await fetch(
    `${RFID_API_URL}/validate?card_id=${encodeURIComponent(cardId)}`
  )
  return res.json()
}

function PlayerDetails({ cardId, info, label }) {
  if (!info?.valid) return null
  const memberNames = (Array.isArray(info.members) ? info.members : [])
    .map((m) => (typeof m === 'string' ? m : m?.name))
    .filter(Boolean)

  return (
    <div className="player-details">
      <div className="player-details-title">{label} — Card validated</div>
      <dl className="player-details-list">
        <div>
          <dt>Card ID</dt>
          <dd>{cardId}</dd>
        </div>
        {memberNames.length > 0 ? (
          <div>
            <dt>Team</dt>
            <dd>
              <ul className="team-members">
                {memberNames.map((name, i) => (
                  <li key={`${name}-${i}`}>{name}</li>
                ))}
              </ul>
            </dd>
          </div>
        ) : (
          <div>
            <dt>Player name</dt>
            <dd>{info.player_name || '—'}</dd>
          </div>
        )}
        <div>
          <dt>Minutes remaining</dt>
          <dd>{info.minutes_remaining ?? '—'}</dd>
        </div>
      </dl>
    </div>
  )
}

export default function LoginScreen({ gameTitle = 'Game', onLogin, playerCount = 1, onBack }) {
  const [card1, setCard1] = useState('')
  const [card2, setCard2] = useState('')
  const [p1Info, setP1Info] = useState(null)
  const [p2Info, setP2Info] = useState(null)
  const [validatedCard1, setValidatedCard1] = useState('')
  const [validatedCard2, setValidatedCard2] = useState('')
  const [error, setError] = useState('')
  const [validating, setValidating] = useState(false)
  const [activeScan, setActiveScan] = useState(1)

  const card1Ref = useRef(null)
  const card2Ref = useRef(null)

  const p1Valid = Boolean(p1Info?.valid)
  const p2Valid = Boolean(p2Info?.valid)
  const canStart = p1Valid && (playerCount === 1 || p2Valid)

  useEffect(() => {
    if (!p1Valid) {
      setActiveScan(1)
      card1Ref.current?.focus()
      return
    }
    if (playerCount === 2 && !p2Valid) {
      setActiveScan(2)
      card2Ref.current?.focus()
    }
  }, [p1Valid, p2Valid, playerCount])

  const runValidate = async (which, rawOverride) => {
    const inputEl = which === 1 ? card1Ref.current : card2Ref.current
    const fallback = which === 1 ? card1 : card2
    const cardId = normalizeCardId(
      rawOverride !== undefined ? rawOverride : (inputEl?.value ?? fallback)
    )

    if (!cardId) {
      setError(which === 1 ? 'Scan Player 1 card' : 'Scan Player 2 card')
      return
    }

    if (which === 1) setCard1(cardId)
    else setCard2(cardId)

    if (playerCount === 2) {
      const other = which === 1
        ? normalizeCardId(card2Ref.current?.value || card2)
        : normalizeCardId(card1Ref.current?.value || card1)
      if (other && cardId === other) {
        setError('Each player needs a different card')
        if (which === 1) {
          setP1Info(null)
          setValidatedCard1('')
        } else {
          setP2Info(null)
          setValidatedCard2('')
        }
        return
      }
    }

    setValidating(true)
    setError('')
    let ok = false
    try {
      const data = await validateRfidCard(cardId)
      ok = Boolean(data.valid)
      if (ok) {
        if (which === 1) {
          setP1Info(data)
          setValidatedCard1(cardId)
        } else {
          setP2Info(data)
          setValidatedCard2(cardId)
        }
      } else {
        if (which === 1) {
          setP1Info(null)
          setValidatedCard1('')
        } else {
          setP2Info(null)
          setValidatedCard2('')
        }
        setError(
          playerCount === 2
            ? `Player ${which}: ${validationError(data)}`
            : validationError(data)
        )
      }
    } catch {
      setError('Could not reach RFID server.')
    } finally {
      setValidating(false)
      requestAnimationFrame(() => {
        if (which === 1 && ok && playerCount === 2) {
          card2Ref.current?.focus()
        } else if (which === 1) {
          card1Ref.current?.focus()
        } else {
          card2Ref.current?.focus()
        }
      })
    }
  }

  const handleCardKeyDown = (which) => (e) => {
    if (e.key !== 'Enter') return
    e.preventDefault()
    e.stopPropagation()
    runValidate(which, e.currentTarget.value)
  }

  const handleCardChange = (which) => (e) => {
    const value = e.target.value
    if (which === 1) {
      setCard1(value)
      setP1Info(null)
      setValidatedCard1('')
    } else {
      setCard2(value)
      setP2Info(null)
      setValidatedCard2('')
    }
    setError('')
  }

  const handleRfidFormSubmit = (e) => {
    e.preventDefault()
  }

  const handleStartGame = () => {
    if (!canStart || validating) return

    if (playerCount === 2 && validatedCard1 === validatedCard2) {
      setError('Each player needs a different card')
      return
    }

    onLogin(
      validatedCard1,
      playerCount === 2 ? validatedCard2 : null,
      p1Info.player_name || '',
      p2Info?.player_name || '',
      p1Info.minutes_remaining ?? null,
      p2Info?.minutes_remaining ?? null
    )
  }

  /** No name form — assign random guest names and start immediately. */
  const handlePlayWithoutRfid = () => {
    const { playerName, playerName2 } = randomGuestNames(playerCount)
    onLogin(
      '',
      playerCount === 2 ? '' : null,
      playerName,
      playerName2,
      null,
      null
    )
  }

  return (
    <div className="screen screen-with-video">
      <VideoBackground />
      <div className="card">
        <h1>{gameTitle}</h1>
        <p className="login-subtitle">
          {playerCount === 2 ? '2-Player Login' : '1-Player Login'}
        </p>

        <form onSubmit={handleRfidFormSubmit}>
          <div className={`input-group scan-field${activeScan === 1 && !p1Valid ? ' ready' : ''}`}>
            <label>Player 1 — Scan RFID Card</label>
            <input
              ref={card1Ref}
              type="text"
              placeholder="Scan card + Enter"
              value={card1}
              onChange={handleCardChange(1)}
              onKeyDown={handleCardKeyDown(1)}
              onFocus={() => setActiveScan(1)}
              autoFocus
              autoComplete="off"
              spellCheck={false}
            />
            {activeScan === 1 && !p1Valid && (
              <p className="scan-hint">Ready to scan</p>
            )}
            <button
              type="button"
              className="btn-validate"
              disabled={validating}
              onClick={() => runValidate(1)}
            >
              Validate card
            </button>
          </div>
          <PlayerDetails cardId={validatedCard1} info={p1Info} label="Player 1" />

          {playerCount === 2 && (
            <>
              <div className={`input-group scan-field${activeScan === 2 && !p2Valid ? ' ready' : ''}`}>
                <label>Player 2 — Scan RFID Card</label>
                <input
                  ref={card2Ref}
                  type="text"
                  placeholder="Scan card + Enter"
                  value={card2}
                  onChange={handleCardChange(2)}
                  onKeyDown={handleCardKeyDown(2)}
                  onFocus={() => setActiveScan(2)}
                  autoComplete="off"
                  spellCheck={false}
                />
                {activeScan === 2 && !p2Valid && (
                  <p className="scan-hint">Ready to scan</p>
                )}
                <button
                  type="button"
                  className="btn-validate"
                  disabled={validating}
                  onClick={() => runValidate(2)}
                >
                  Validate card
                </button>
              </div>
              <PlayerDetails cardId={validatedCard2} info={p2Info} label="Player 2" />
            </>
          )}

          {validating && <p className="login-status">Validating…</p>}
          {error && <div className="error">{error}</div>}

          <button
            type="button"
            className="btn-start"
            disabled={!canStart || validating}
            onClick={handleStartGame}
          >
            Start Game
          </button>
          <button
            type="button"
            className="btn-muted"
            onClick={handlePlayWithoutRfid}
          >
            Play without RFID
          </button>
          {onBack && (
            <button type="button" className="btn-muted" onClick={onBack}>
              Back
            </button>
          )}
        </form>
      </div>
    </div>
  )
}
