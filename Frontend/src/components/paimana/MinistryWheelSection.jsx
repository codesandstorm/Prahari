import React, { useState } from 'react';
import { MINISTRIES, SECTORS } from '../../data/paimanaStaticData';

const VISIBLE_ITEMS = 4;

function StatCard({ title, note, children }) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad project-count"
      style={{ position: 'relative' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {children}
      {hovered && note && (
        <div
          className="listhover listbottom"
          style={{
            display: 'block',
            position: 'absolute',
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 100,
            background: '#fff',
            border: '1px solid #ccc',
            borderRadius: 6,
            padding: '6px 10px',
            whiteSpace: 'nowrap',
            boxShadow: '0 2px 8px rgba(0,0,0,.15)',
            fontSize: 12,
          }}
        >
          <h6 style={{ margin: 0 }}>{note}</h6>
        </div>
      )}
    </div>
  );
}

function WheelStatDisplay({ stats, title }) {
  return (
    <div className="row shadow-lg p-3 bg-body rounded wheelbox wheelproject">
      <h3 className="text-center py-3 heading brd-btm crd-bg-clr text-white">{title}</h3>

      <div className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad project-count">
        <img src="/Paimana_Files/project-count.png" alt="" />
        <div className="text-center m-0">
          <p className="count-head py-2 d-inline-block">Project Count <span>(No.)</span></p>
          <h5 className="project-count1"><label>{stats.count}</label></h5>
        </div>
      </div>

      <div className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad project-count">
        <img src="/Paimana_Files/orginal-cost.png" alt="" />
        <div className="text-center m-0">
          <p className="count-head py-2 d-inline-block">Original Cost <span>(in Cr)</span></p>
          <h5 className="project-count1"><label>{stats.originalCost}</label></h5>
        </div>
      </div>

      <div className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad project-count">
        <img src="/Paimana_Files/revised-cost.png" alt="" />
        <div className="text-center m-0">
          <p className="count-head py-2 d-inline-block">Latest Revised Cost <span>(in Cr)</span></p>
          <h5 className="project-count1"><label>{stats.revisedCost}</label></h5>
        </div>
      </div>

      <div className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad project-count">
        <img src="/Paimana_Files/expenditure.png" alt="" />
        <div className="text-center m-0">
          <p className="count-head py-2 d-inline-block">Expenditure(Cumm.) <span>(in Cr)</span></p>
          <h5 className="project-count1"><label>{stats.expenditure}</label></h5>
        </div>
      </div>

      <div className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad Completed_Project">
        <img src="/Paimana_Files/compliance-year.png" alt="" />
        <div className="text-center m-0">
          <p className="count-head py-2 d-inline-block">Completed During Month <span>(No.)</span></p>
          <h5 className="project-count1"><label>{stats.completedMonth}</label></h5>
        </div>
      </div>

      <div className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad New_Added">
        <img src="/Paimana_Files/new-project.png" alt="" />
        <div className="text-center m-0">
          <p className="count-head py-2 d-inline-block">Newly Added <span>(No.)</span></p>
          <h5 className="project-count1"><label>{stats.newlyAdded}</label></h5>
        </div>
      </div>
    </div>
  );
}

export default function MinistryWheelSection() {
  const [activeTab, setActiveTab] = useState('ministry'); // 'ministry' | 'state' (sector)
  const [ministryOffset, setMinistryOffset] = useState(0);
  const [sectorOffset, setSectorOffset] = useState(0);
  const [activeMinistry, setActiveMinistry] = useState(MINISTRIES[6]); // DHE (matching original)
  const [activeSector, setActiveSector] = useState(SECTORS[8]); // Telecommunication (matching original)

  /* ── Ministry helpers ── */
  const visibleMinistries = MINISTRIES.slice(ministryOffset, ministryOffset + VISIBLE_ITEMS);
  const canPrevMinistry = ministryOffset > 0;
  const canNextMinistry = ministryOffset + VISIBLE_ITEMS < MINISTRIES.length;

  /* ── Sector helpers ── */
  const visibleSectors = SECTORS.slice(sectorOffset, sectorOffset + VISIBLE_ITEMS);
  const canPrevSector = sectorOffset > 0;
  const canNextSector = sectorOffset + VISIBLE_ITEMS < SECTORS.length;

  return (
    <section className="atomiconmob position-relative wheelalternative" id="WheelSection">
      <div id="WhellView">
        <div className="container-fluid">
          <div className="row">
            <div className="col-sm-12 col-md-12 col-xl-12">
              {/* Tab buttons */}
              <ul className="nav nav-tabs" id="myTab" role="tablist">
                <li className="nav-item" role="presentation">
                  <button
                    className={`nav-link${activeTab === 'ministry' ? ' active' : ''}`}
                    id="ministry-tab"
                    role="tab"
                    onClick={() => setActiveTab('ministry')}
                  >
                    Ministry-wise
                  </button>
                </li>
                <li className="nav-item" role="presentation">
                  <button
                    className={`nav-link${activeTab === 'state' ? ' active' : ''}`}
                    id="state-tab"
                    role="tab"
                    onClick={() => setActiveTab('state')}
                  >
                    Sector-wise
                  </button>
                </li>
              </ul>

              <div className="tab-content" id="myTabContent">
                {/* ── Ministry Tab ── */}
                <div
                  className={`tab-pane fade${activeTab === 'ministry' ? ' show active' : ''}`}
                  id="ministry"
                  role="tabpanel"
                >
                  <div className="row pt-2 mx-5 align-items-center">
                    {/* List */}
                    <div className="col-sm-12 col-md-4 col-xl-3 pt-2">
                      <div className="tablistwheelsector text-center">
                        <button
                          id="prev001M"
                          onClick={() => setMinistryOffset((o) => Math.max(0, o - 1))}
                          disabled={!canPrevMinistry}
                        >
                          <img src="/Paimana_Files/prev-icon-1.png" alt="Previous" />
                        </button>
                        <div className="sectordetails">
                          <div className="ministriesdetails">
                            <div className="ministrieslist">
                              {visibleMinistries.map((m) => (
                                <a
                                  key={m.id}
                                  href="#WheelSection"
                                  className={activeMinistry.id === m.id ? 'active' : ''}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    setActiveMinistry(m);
                                  }}
                                >
                                  {m.shortName}
                                </a>
                              ))}
                            </div>
                          </div>
                        </div>
                        <button
                          id="next001M"
                          onClick={() =>
                            setMinistryOffset((o) =>
                              o + VISIBLE_ITEMS < MINISTRIES.length ? o + 1 : o
                            )
                          }
                          disabled={!canNextMinistry}
                        >
                          <img src="/Paimana_Files/next-icon-1.png" alt="Next" />
                        </button>
                      </div>
                    </div>

                    {/* Stats card */}
                    <div className="col-sm-12 col-md-8 col-xl-6 text-center">
                      <div className="slides_txt">
                        <div className="tabcontent01">
                          <WheelStatDisplay
                            stats={activeMinistry.stats}
                            title={activeMinistry.fullName}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Logo image */}
                    <div className="col-sm-12 col-md-12 col-xl-3 text-center m-0">
                      <div className="text-center m-0">
                        <img
                          id="ministryImage"
                          src={`/Paimana_Files/${activeMinistry.imgFile}`}
                          className="extrahgtimg"
                          alt={activeMinistry.shortName}
                          onError={(e) => (e.currentTarget.style.display = 'none')}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* ── Sector Tab ── */}
                <div
                  className={`tab-pane fade${activeTab === 'state' ? ' show active' : ''}`}
                  id="state"
                  role="tabpanel"
                >
                  <div className="row pt-2 mx-5 align-items-center">
                    {/* List */}
                    <div className="col-sm-12 col-md-4 col-xl-3 pt-2">
                      <div className="tablistwheelsector text-center">
                        <button
                          id="prev001S"
                          onClick={() => setSectorOffset((o) => Math.max(0, o - 1))}
                          disabled={!canPrevSector}
                        >
                          <img src="/Paimana_Files/prev-icon-1.png" alt="Previous" />
                        </button>
                        <div className="sectordetails">
                          <div className="sectorlist">
                            {visibleSectors.map((s) => (
                              <a
                                key={s.id}
                                href="#WheelSection"
                                className={activeSector.id === s.id ? 'active' : ''}
                                onClick={(e) => {
                                  e.preventDefault();
                                  setActiveSector(s);
                                }}
                              >
                                {s.shortName}
                              </a>
                            ))}
                          </div>
                        </div>
                        <button
                          id="next001S"
                          onClick={() =>
                            setSectorOffset((o) =>
                              o + VISIBLE_ITEMS < SECTORS.length ? o + 1 : o
                            )
                          }
                          disabled={!canNextSector}
                        >
                          <img src="/Paimana_Files/next-icon-1.png" alt="Next" />
                        </button>
                      </div>
                    </div>

                    {/* Stats card */}
                    <div className="col-sm-12 col-md-8 col-xl-6 text-center">
                      <div className="slides_txt">
                        <div className="tabcontent01">
                          <div className="row shadow-lg p-3 bg-body rounded wheelbox wheelproject">
                            <h3 className="text-center py-3 heading brd-btm crd-bg-clr text-white">
                              {activeSector.shortName}{' '}
                              <small style={{ fontWeight: 'normal', fontSize: '0.7em' }}>
                                (As of July, 2026)
                              </small>
                            </h3>
                            {[
                              { img: 'project-count.png',    label: 'Project Count',             sub: '(No.)',    val: activeSector.stats.count },
                              { img: 'orginal-cost.png',     label: 'Original Cost',             sub: '(in Cr)',  val: activeSector.stats.originalCost },
                              { img: 'revised-cost.png',     label: 'Latest Revised Cost',       sub: '(in Cr)',  val: activeSector.stats.revisedCost },
                              { img: 'expenditure.png',      label: 'Expenditure(Cumm.)',         sub: '(in Cr)',  val: activeSector.stats.expenditure },
                              { img: 'compliance-year.png',  label: 'Completed During Month',    sub: '(No.)',    val: activeSector.stats.completedMonth },
                              { img: 'new-project.png',      label: 'Newly Added',               sub: '(No.)',    val: activeSector.stats.newlyAdded },
                            ].map(({ img, label, sub, val }) => (
                              <div key={label} className="col-xl-4 col-md-12 col-sm-12 d-flex text-center extrapad project-count11">
                                <img src={`/Paimana_Files/${img}`} alt={label} />
                                <div className="text-center m-0">
                                  <p className="count-head py-2 d-inline-block">{label} <span>{sub}</span></p>
                                  <h5 className="project-count11"><label>{val}</label></h5>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Sector image */}
                    <div className="col-sm-12 col-md-12 col-xl-3 text-center m-0">
                      <div className="text-center m-0">
                        <img
                          id="sectorImage"
                          src={`/Paimana_Files/${activeSector.imgFile}`}
                          className="extrahgtimg"
                          alt={activeSector.shortName}
                          onError={(e) => (e.currentTarget.style.display = 'none')}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Project Monitoring ribbon icon */}
      <div className="projectmointering rgt">
        <img
          src="/Paimana_Files/project-mointering-1.svg"
          alt="Project Monitoring"
          width="60"
        />
      </div>
    </section>
  );
}
