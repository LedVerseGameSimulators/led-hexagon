/** Client-side play/RFID context for reload resume (Step 0 Round 2). */
const KEY = 'led_hex_active_game_ctx'

export function persistGameResumeContext(gameId, config) {
  const id = String(gameId ?? '').trim()
  if (!id) return
  try {
    sessionStorage.setItem(
      KEY,
      JSON.stringify({
        game_id: id,
        playMode: config.playMode,
        playerCount: config.playerCount,
        cardId: config.cardId,
        cardId2: config.cardId2,
        rfidValidate1: config.rfidValidate1,
        rfidValidate2: config.rfidValidate2,
        playerName: config.playerName,
        playerName2: config.playerName2,
        minutesRemaining: config.minutesRemaining,
        minutesRemaining2: config.minutesRemaining2,
      })
    )
  } catch {
    /* quota / private mode */
  }
}

/** Returns stored context only when game_id matches resumeGameId. */
export function loadGameResumeContext(resumeGameId) {
  const id = String(resumeGameId ?? '').trim()
  if (!id) return null
  try {
    const raw = sessionStorage.getItem(KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed?.game_id !== id) return null
    return parsed
  } catch {
    return null
  }
}

export function clearGameResumeContext(gameId) {
  try {
    const raw = sessionStorage.getItem(KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    const id = String(gameId ?? '').trim()
    if (!id || parsed?.game_id === id) {
      sessionStorage.removeItem(KEY)
    }
  } catch {
    sessionStorage.removeItem(KEY)
  }
}
