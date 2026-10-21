import { RFID_API_URL } from './config'

/** Map setup playMode to RFID play_mode (STEP0 contract). */
export function playModeToRfidPlayMode(playMode) {
  switch (playMode) {
    case 'multi':
      return 'team_battle'
    case 'group':
      return 'tournament'
    case 'single':
    default:
      return 'quick_play'
  }
}

/** Extract slot-1/2 context fields from a /validate JSON body. */
export function slotContextFromValidate(data) {
  if (!data || !data.valid) {
    return {
      session_id: null,
      group_id: null,
      roster_size_at_play: null,
      roster_player_ids: null,
    }
  }
  let rosterIds = data.roster_player_ids
  if (!Array.isArray(rosterIds) && Array.isArray(data.members)) {
    rosterIds = data.members
      .map((m) => (typeof m === 'object' && m != null ? m.player_id ?? m.id : null))
      .filter((id) => id != null)
  }
  return {
    session_id: data.session_id ?? null,
    group_id: data.group_id ?? null,
    roster_size_at_play:
      data.roster_size != null ? data.roster_size : (Array.isArray(rosterIds) ? rosterIds.length : null),
    roster_player_ids: Array.isArray(rosterIds) ? rosterIds : null,
  }
}

const VALIDATE_TIMEOUT_MS = 2000

/** Best-effort refresh; never throws. Returns null on failure/timeout. */
export async function refreshValidate(cardId) {
  const id = String(cardId ?? '').trim()
  if (!id) return null
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), VALIDATE_TIMEOUT_MS)
  try {
    const res = await fetch(
      `${RFID_API_URL}/validate?card_id=${encodeURIComponent(id)}`,
      { signal: controller.signal }
    )
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Team Battle only: two distinct leader cards. Hex backend may set multiplayer=false
 * on the last .led level in a .ledb chain (L33); slot-2 must not rely on that flag.
 */
export function teamBattleCardId2(config) {
  if (config?.playMode !== 'multi') return null
  const c1 = String(config.cardId ?? '').trim()
  const c2 = String(config.cardId2 ?? '').trim()
  if (!c1 || !c2 || c1.toLowerCase() === c2.toLowerCase()) return null
  return c2
}

/** Merge login-time validate payload with optional end-game refresh. */
export function resolveSlotContext(loginValidate, refreshedValidate) {
  const fromRefresh = slotContextFromValidate(refreshedValidate)
  const fromLogin = slotContextFromValidate(loginValidate)
  const pick = (key) => {
    const r = fromRefresh[key]
    if (r != null && r !== '') return r
    return fromLogin[key]
  }
  return {
    session_id: pick('session_id'),
    group_id: pick('group_id'),
    roster_size_at_play: pick('roster_size_at_play'),
    roster_player_ids: pick('roster_player_ids'),
  }
}
