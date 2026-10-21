import { useState, useEffect } from 'react'
import SetupScreen     from './screens/SetupScreen'
import LoginScreen     from './screens/LoginScreen'
import CountdownScreen from './screens/CountdownScreen'
import SimulatorScreen from './screens/SimulatorScreen'
import ResultScreen    from './screens/ResultScreen'

import { API_URL } from './config'
import { loadGameResumeContext } from './gameResumeStorage'
import VideoBackground from './components/VideoBackground'

const S = {
  SETUP:     'setup',      // Mode + Level (one screen)
  LOGIN:     'login',
  COUNTDOWN: 'countdown',
  SIMULATOR: 'simulator',
  RESULT:    'result',
}

const DEFAULT_CONFIG = {
  game: 'led_hex',
  playMode: 'single',
  level: '03',
  playerCount: 1,
  difficulty: 'normal',
  cardId: '',
  cardId2: '',
  playerName: '',
  playerName2: '',
  minutesRemaining: null,
  minutesRemaining2: null,
  rfidValidate1: null,
  rfidValidate2: null,
}

export default function App() {
  const [screen, setScreen] = useState(S.SETUP)
  const [gameConfig, setGameConfig] = useState(DEFAULT_CONFIG)
  const [result, setResult] = useState(null)
  const [booting, setBooting] = useState(true)
  const [playlists, setPlaylists] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/playlists`)
      .then((r) => r.json())
      .then((data) => setPlaylists(data))
      .catch((err) => console.warn('playlists fetch failed:', err))
  }, [])

  useEffect(() => {
    fetch(`${API_URL}/active-game`)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          const restored = loadGameResumeContext(d.game_id)
          setGameConfig((prev) => ({
            ...prev,
            cardId: restored?.cardId || d.card_id,
            level: d.level,
            difficulty: d.difficulty,
            resumeGameId: d.game_id,
            ...(restored && restored.game_id === d.game_id
              ? {
                  playMode: restored.playMode ?? prev.playMode,
                  playerCount: restored.playerCount ?? prev.playerCount,
                  cardId2: restored.cardId2 ?? '',
                  rfidValidate1: restored.rfidValidate1 ?? null,
                  rfidValidate2: restored.rfidValidate2 ?? null,
                  playerName: restored.playerName ?? '',
                  playerName2: restored.playerName2 ?? '',
                  minutesRemaining: restored.minutesRemaining ?? null,
                  minutesRemaining2: restored.minutesRemaining2 ?? null,
                }
              : {}),
          }))
          setScreen(S.SIMULATOR)
        }
      })
      .catch(() => {})
      .finally(() => setBooting(false))
  }, [])

  // Setup confirmed (mode + level together)
  const handleSetup = ({ game, level, playerCount, difficulty, playMode }) => {
    setGameConfig((prev) => ({
      ...prev,
      game,
      level,
      playerCount,
      difficulty,
      playMode: playMode || prev.playMode,
      resumeGameId: undefined,
    }))
    setScreen(S.LOGIN)
  }

  const handleLogin = (
    cardId,
    cardId2,
    playerName = '',
    playerName2 = '',
    minutesRemaining = null,
    minutesRemaining2 = null,
    rfidValidate1 = null,
    rfidValidate2 = null
  ) => {
    setGameConfig((prev) => ({
      ...prev,
      cardId: cardId || '',
      cardId2: cardId2 || '',
      playerName: playerName || '',
      playerName2: playerName2 || '',
      minutesRemaining,
      minutesRemaining2,
      rfidValidate1: rfidValidate1?.valid ? rfidValidate1 : null,
      rfidValidate2: rfidValidate2?.valid ? rfidValidate2 : null,
    }))
    setScreen(S.COUNTDOWN)
  }

  const handleCountdownDone = () => setScreen(S.SIMULATOR)

  const handleGameEnd = (finalResult) => {
    setResult(finalResult)
    setScreen(S.RESULT)
  }

  const handlePlayAgain = () => {
    setResult(null)
    setScreen(S.SETUP)
  }

  const handleLogout = () => {
    setResult(null)
    setGameConfig({ ...DEFAULT_CONFIG })
    setScreen(S.SETUP)
  }

  if (booting) {
    return (
      <div className="screen screen-with-video">
        <VideoBackground />
        <div className="card">
          <h2 style={{ textAlign: 'center' }}>Loading…</h2>
        </div>
      </div>
    )
  }

  return (
    <>
      {screen === S.SETUP && (
        <SetupScreen
          game={gameConfig.game}
          playlists={playlists}
          onConfirm={handleSetup}
        />
      )}
      {screen === S.LOGIN && (
        <LoginScreen
          gameTitle="Battle Arena"
          playerCount={gameConfig.playerCount}
          onLogin={handleLogin}
          onBack={() => setScreen(S.SETUP)}
        />
      )}
      {screen === S.COUNTDOWN && (
        <CountdownScreen onDone={handleCountdownDone} />
      )}
      {screen === S.SIMULATOR && (
        <SimulatorScreen
          config={gameConfig}
          playlists={playlists}
          onGameEnd={handleGameEnd}
        />
      )}
      {screen === S.RESULT && (
        <ResultScreen
          result={result}
          config={gameConfig}
          playlists={playlists}
          onPlayAgain={handlePlayAgain}
          onLogout={handleLogout}
        />
      )}
    </>
  )
}
