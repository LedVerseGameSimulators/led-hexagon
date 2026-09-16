import VideoBackground from '../components/VideoBackground'

const MODES = [
  {
    id: 'single',
    title: 'Quick Play',
    desc: 'Solo · 20 levels · Medium',
    icon: '1',
  },
  {
    id: 'multi',
    title: 'Team Battle',
    desc: '2 players · 20 levels · Medium',
    icon: '2',
  },
  {
    id: 'group',
    title: 'Tournament',
    desc: 'Group session · fixed level set',
    icon: 'T',
  },
]

export default function GameSelectionScreen({ onSelect, loading = false }) {
  return (
    <div className="screen screen-with-video">
      <VideoBackground />
      <div className="landing">
        <header className="landing-hero">
          <h1 className="landing-brand">ACTIVERSE</h1>
          <p className="landing-product">Battle Arena</p>
          <p className="landing-tagline">
            {loading ? 'Loading…' : 'Choose how you want to play'}
          </p>
        </header>

        <div className="mode-grid" aria-busy={loading || undefined}>
          {MODES.map((mode) => (
            <button
              key={mode.id}
              type="button"
              className="mode-card"
              disabled={loading}
              onClick={() => onSelect(mode.id)}
            >
              <span className="mode-card-icon" aria-hidden="true">{mode.icon}</span>
              <span className="mode-card-text">
                <span className="mode-card-title">{mode.title}</span>
                <span className="mode-card-desc">{mode.desc}</span>
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
