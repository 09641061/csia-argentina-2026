import { NavLink, Outlet } from 'react-router-dom'

const NAVIGATION = [
  { to: '/', label: 'Consultar', end: true },
  { to: '/historial', label: 'Historial', end: false },
]

export function AppLayout() {
  return (
    <div className="app">
      <header className="app__header">
        <div className="app__header-inner">
          <NavLink className="app__brand" to="/">
            Sentinel AI Guard
          </NavLink>
          <nav className="app__nav" aria-label="Navegación principal">
            {NAVIGATION.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? 'app__nav-link app__nav-link--active' : 'app__nav-link'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="app__main">
        <Outlet />
      </main>
    </div>
  )
}
