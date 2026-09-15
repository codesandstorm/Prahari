import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export default function PaimanaHeader() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dropdown, setDropdown] = useState(null); // 'publications' | 'dashboard' | 'prahari'

  const toggleDropdown = (name) =>
    setDropdown((prev) => (prev === name ? null : name));

  return (
    <>
      {/* ── Desktop Header ─────────────────────────────────────── */}
      <header className="position-relative">
        {/* Topbar */}
        <div className="topbar">
          <div className="container">
            <div className="topbarbox">
              <div className="topbar-actions">
                <a
                  href="#mainPage"
                  className="topbar-skip"
                  title="Skip to Main Content"
                  aria-label="Skip to Main Content"
                >
                  <img
                    src="/Paimana_Files/skip_to_main.svg"
                    alt="Skip to Main Content"
                    className="topbar-icon"
                  />
                  <span className="topbar-skip-text">Skip to Main Content</span>
                </a>
                <button
                  className="topbar-icon-btn topbar-lang"
                  type="button"
                  title="Language"
                  aria-label="Language"
                >
                  <img
                    src="/Paimana_Files/hind-english.svg"
                    alt="Language"
                    className="topbar-icon"
                  />
                </button>
                <div className="dropdown topbar-access">
                  <button
                    className="topbar-icon-btn"
                    type="button"
                    title="Accessibility / Font Size"
                    aria-label="Accessibility / Font Size"
                  >
                    <img
                      src="/Paimana_Files/accessiblity.svg"
                      alt="Accessibility"
                      className="topbar-icon"
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Logo row */}
        <div className="container">
          <div className="header-flex-row">
            <div className="header-left-group">
              <a
                href="https://www.mospi.gov.in/"
                target="_blank"
                rel="noreferrer"
                className="ministry-block"
              >
                <img
                  src="/Paimana_Files/logo-mospi.png"
                  alt="Ministry of Statistics and Programme Implementation"
                  className="ministry-text-img"
                />
              </a>
              <div className="partner-logos">
                <a
                  href="https://www.dic.gov.in/"
                  target="_blank"
                  rel="noreferrer"
                  title="Data for Development"
                >
                  <img
                    src="/Paimana_Files/data-for-dev.png"
                    alt="Data for Development"
                    onError={(e) => (e.currentTarget.style.display = 'none')}
                  />
                </a>
              </div>
            </div>
            <div className="header-right-group">
              <ul className="headerlist">
                <li>
                  <a
                    href="https://paimana-crip.mospi.gov.in/"
                    target="_blank"
                    rel="noreferrer"
                    className="haddProject"
                  >
                    Add Project / Update
                  </a>
                </li>
                <li>
                  <a
                    href="https://paimana-proj.mospi.gov.in/User/Login"
                    className="hlogin"
                  >
                    Reports
                  </a>
                </li>
              </ul>
            </div>
            <a
              href="https://paimana.mospi.gov.in/"
              target="_blank"
              rel="noreferrer"
              className="paimana-brand"
            >
              <img src="/Paimana_Files/logo-paimana.png" alt="PAIMANA" />
            </a>
          </div>
        </div>
      </header>

      {/* ── Mobile Header ───────────────────────────────────────── */}
      <div className="mobileheader">
        <div className="container-fluid">
          <div className="mospiheader">
            <div className="boxone">
              <div className="menulink">
                <button
                  style={{ background: 'none', border: 'none', padding: 0 }}
                  onClick={() => setMobileMenuOpen(true)}
                  aria-label="Open Menu"
                >
                  <img
                    src="/Paimana_Files/side_menu-dark.png"
                    alt="Mobile Side Icon"
                  />
                </button>
              </div>
              <div className="mospiname">IPMD | MoSPI</div>
            </div>
            <div className="boxone two">
              <div className="moblogin">
                <a href="https://paimana-proj.mospi.gov.in/User/Login">
                  Login{' '}
                  <img src="/Paimana_Files/login.png" alt="Login" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile offcanvas */}
      {mobileMenuOpen && (
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            display: 'flex',
          }}
        >
          <div
            style={{ flex: 1, background: 'rgba(0,0,0,0.5)' }}
            onClick={() => setMobileMenuOpen(false)}
          />
          <div
            style={{
              width: 280, background: '#fff', height: '100%',
              overflowY: 'auto', padding: '20px', boxShadow: '-2px 0 8px rgba(0,0,0,.2)',
            }}
          >
            <button
              onClick={() => setMobileMenuOpen(false)}
              style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', marginBottom: 20 }}
            >
              ×
            </button>
            <nav>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                <li style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                  <Link to="/" onClick={() => setMobileMenuOpen(false)}>Home</Link>
                </li>
                <li style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                  <a href="https://paimana-proj.mospi.gov.in/ReportPage" target="_blank" rel="noreferrer">Publications</a>
                </li>
                <li style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                  <a href="https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew" target="_blank" rel="noreferrer">Dashboard</a>
                </li>
                <li style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                  <Link to="/prahari" onClick={() => setMobileMenuOpen(false)}>PRAHARI Intelligence</Link>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      )}

      {/* ── Desktop Navbar ──────────────────────────────────────── */}
      <section className="desktopshow navigationmenu">
        <div className="row bg-secondry">
          <nav className="navbar navbar-expand-lg bg-body-tertiary bg-secondry">
            <div className="container-fluid">
              <div className="collapse navbar-collapse navMenu float-left" id="navbarNavDropdown">
                <ul className="navbar-nav">
                  {/* Home */}
                  <li className="nav-item">
                    <Link className="nav-link" to="/">Home</Link>
                  </li>

                  {/* Publications dropdown */}
                  <li className="nav-item dropdown">
                    <button
                      className="nav-link dropdown-toggle"
                      style={{ background: 'none', border: 'none' }}
                      onClick={() => toggleDropdown('publications')}
                    >
                      Publications
                    </button>
                    {dropdown === 'publications' && (
                      <ul className="dropdown-menu show">
                        <li>
                          <a className="dropdown-item" href="https://paimana-proj.mospi.gov.in/ReportPage" target="_blank" rel="noreferrer">
                            Project Monitoring
                          </a>
                        </li>
                        <li>
                          <a className="dropdown-item" href="https://paimana-proj.mospi.gov.in/ProjectMonitoring" target="_blank" rel="noreferrer">
                            Performance Monitoring
                          </a>
                        </li>
                      </ul>
                    )}
                  </li>

                  {/* Dashboard dropdown */}
                  <li className="nav-item dropdown">
                    <button
                      className="nav-link dropdown-toggle"
                      style={{ background: 'none', border: 'none' }}
                      onClick={() => toggleDropdown('dashboard')}
                    >
                      Dashboard
                    </button>
                    {dropdown === 'dashboard' && (
                      <ul className="dropdown-menu show">
                        <li>
                          <a className="dropdown-item" href="https://paimana-proj.mospi.gov.in/Home/PublicDashboardNew" target="_blank" rel="noreferrer">
                            Public
                          </a>
                        </li>
                      </ul>
                    )}
                  </li>

                  {/* PRAHARI Intelligence dropdown */}
                  <li className="nav-item dropdown">
                    <button
                      className="nav-link dropdown-toggle"
                      id="prahariNavigation"
                      style={{ background: 'none', border: 'none' }}
                      onClick={() => toggleDropdown('prahari')}
                    >
                      PRAHARI Intelligence
                    </button>
                    {dropdown === 'prahari' && (
                      <ul className="dropdown-menu show">
                        <li><Link className="dropdown-item" to="/prahari" onClick={() => setDropdown(null)}>Officer Dashboard</Link></li>
                        <li><Link className="dropdown-item" to="/prahari/review-queue" onClick={() => setDropdown(null)}>Review Queue</Link></li>
                        <li><Link className="dropdown-item" to="/prahari/analytics" onClick={() => setDropdown(null)}>Portfolio Analytics</Link></li>
                        <li><Link className="dropdown-item" to="/prahari/data-trust" onClick={() => setDropdown(null)}>Data Trust / Verification</Link></li>
                        <li><Link className="dropdown-item" to="/prahari/model-validation" onClick={() => setDropdown(null)}>Model Validation</Link></li>
                        <li><Link className="dropdown-item" to="/prahari/cuf-sandbox" onClick={() => setDropdown(null)}>CUF Sandbox</Link></li>
                        <li><Link className="dropdown-item" to="/prahari/assistant" onClick={() => setDropdown(null)}>Ask PRAHARI</Link></li>
                      </ul>
                    )}
                  </li>
                </ul>
              </div>
            </div>
          </nav>
        </div>
      </section>
    </>
  );
}
