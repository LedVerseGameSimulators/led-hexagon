/**
 * Placeholder playlists for Hex FE redesign.
 * Real 20-level lists will replace these when the team delivers them.
 * Backend still receives real file ids (stems); UI may show 1..N.
 */

/** Quick Play (1P) — 20 medium-ish placeholders from Pro + Advanced. */
export const QUICK_PLAY_LEVELS = [
  '00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
  '10', '11', '12', '13', '14', '15', '16', 'YC01', 'YC02', 'YC03',
]

/** Team Battle (2P) — 20 placeholders from DK + YCDK. */
export const TEAM_BATTLE_LEVELS = [
  'DK01', 'DK02', 'DK03', 'DK04', 'DK05', 'DK06', 'DK07', 'DK08', 'DK09', 'DK10',
  'DK11', 'YCDK02', 'YCDK03', 'YCDK04', 'YCDK05', 'YCDK06', 'YCDK07', 'YCDK08',
  'YCDK09', 'YCDK10',
]

/**
 * Tournament playlist order (matches games/source_group README /
 * _build_group_level_sequence: - then --).
 */
export const TOURNAMENT_LEVEL_ORDER = [
  '05', '06', '07', '08', '09',
  'YC01', 'YC02', 'YC03', 'YC04', 'YC05',
]

export const HOW_TO = {
  single:
    'Step on glowing hex tiles that match the goal colour. Avoid red hazards. Clear each wave to advance.',
  multi:
    'Each player scores their own colour. Watch the floor — red hurts both. Clear your targets to progress.',
  group:
    'A fixed set of levels runs in order. No level pick — just play through 1, 2, 3… as a group session.',
}

export function playlistForMode(playMode) {
  if (playMode === 'multi') return TEAM_BATTLE_LEVELS
  if (playMode === 'group') return TOURNAMENT_LEVEL_ORDER
  return QUICK_PLAY_LEVELS
}

/** Map backend level stem → UI number (1-based) within the active playlist. */
export function displayLevelNumber(playMode, levelId) {
  const stem = String(levelId ?? '')
    .replace(/\.(led|ledb)$/i, '')
    .trim()
  if (!stem || stem === 'auto') return null
  const list = playlistForMode(playMode)
  const idx = list.findIndex(
    (id) => id === stem || stem.startsWith(id) || id.startsWith(stem)
  )
  if (idx >= 0) return idx + 1
  // Fallback: numeric stems display as themselves when in tournament-style lists
  if (/^\d+$/.test(stem)) return Number(stem)
  return null
}

export function formatLevelLabel(playMode, levelId) {
  const n = displayLevelNumber(playMode, levelId)
  if (n != null) return String(n)
  return String(levelId ?? '—')
}
