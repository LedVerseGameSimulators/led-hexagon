import { useMemo, useState } from 'react'

import VideoBackground from '../components/VideoBackground'
import {
  HOW_TO,
  QUICK_PLAY_LEVELS,
  TEAM_BATTLE_LEVELS,
} from '../levelPlaylists'

export default function GameSettingsScreen({
  game,
  playerCount,
  playMode = 'single',
  onConfirm,
  onBack,
}) {
  const players = playerCount ?? 1
  const ids = players === 2 ? TEAM_BATTLE_LEVELS : QUICK_PLAY_LEVELS
  const [selectedIndex, setSelectedIndex] = useState(0)

  const howTo = useMemo(
    () => (players === 2 ? HOW_TO.multi : HOW_TO.single),
    [players]
  )

  const selectedId = ids[selectedIndex] || ids[0]

  const handleConfirm = () => {
    if (!selectedId) return
    onConfirm({
      game,
      level: selectedId,
      levelData: { id: selectedId, name: String(selectedIndex + 1) },
      playerCount: players,
      // Locked product: treat as medium without extra difficulty UI
      difficulty: 'normal',
      playMode,
    })
  }

  return (
    <div className="screen screen-with-video">
      <VideoBackground />
      <div className="card settings-card">
        <h1>Battle Arena</h1>
        <p className="settings-subtitle">
          {players === 2 ? 'Team Battle' : 'Quick Play'} · Select level · Medium
        </p>

        <h2 className="settings-section-label">
          LEVEL <span className="settings-count">({ids.length})</span>
        </h2>
        <div className="level-grid" role="listbox" aria-label="Levels">
          {ids.map((id, i) => (
            <button
              key={id}
              type="button"
              role="option"
              aria-selected={selectedIndex === i}
              className={`level-grid-btn ${selectedIndex === i ? 'selected' : ''}`}
              onClick={() => setSelectedIndex(i)}
              title={id}
            >
              {i + 1}
            </button>
          ))}
        </div>

        <h2 className="settings-section-label">HOW TO PLAY</h2>
        <p className="how-to-copy">{howTo}</p>

        <button type="button" onClick={handleConfirm} style={{ marginTop: '24px' }}>
          Next → Login
        </button>
        <button type="button" onClick={onBack} className="btn-secondary" style={{ marginTop: '10px' }}>
          Back
        </button>
      </div>
    </div>
  )
}
