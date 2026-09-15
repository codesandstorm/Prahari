import React, { useState, useEffect, useRef } from 'react';
import { HIGH_VALUE_PROJECTS } from '../../data/paimanaStaticData';

const VISIBLE = 4;
const AUTO_SLIDE_INTERVAL = 3500;

export default function HighValueProjectsCarousel() {
  const [start, setStart] = useState(0);
  const [paused, setPaused] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (paused) {
      clearInterval(intervalRef.current);
      return;
    }
    intervalRef.current = setInterval(() => {
      setStart((s) => {
        const next = s + 1;
        return next + VISIBLE > HIGH_VALUE_PROJECTS.length ? 0 : next;
      });
    }, AUTO_SLIDE_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, [paused]);

  const canPrev = start > 0;
  const canNext = start + VISIBLE < HIGH_VALUE_PROJECTS.length;

  const visible = HIGH_VALUE_PROJECTS.slice(start, start + VISIBLE);

  return (
    <section
      style={{ padding: '30px 0', background: '#f8f9fa' }}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div className="container-fluid">
        {/* Heading row */}
        <div className="row" style={{ marginBottom: 20 }}>
          <div className="col text-center">
            <h2 style={{ fontWeight: 700, color: '#0b1c3b' }}>High-Value Projects</h2>
          </div>
          {/* Prev / Next buttons — both always active, wrap-around */}
          <div className="col-auto d-flex align-items-center" style={{ gap: 10 }}>
            <button
              aria-label="Previous"
              onClick={() => setStart((s) => (s - 1 < 0 ? HIGH_VALUE_PROJECTS.length - VISIBLE : s - 1))}
              style={{
                background: '#0b1c3b',
                border: 'none',
                borderRadius: '50%',
                width: 36,
                height: 36,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img src="/Paimana_Files/prev-icon-1.png" alt="Prev" style={{ width: 18, filter: 'invert(1)' }} />
            </button>
            <button
              aria-label="Next"
              onClick={() => setStart((s) => (s + 1 + VISIBLE > HIGH_VALUE_PROJECTS.length ? 0 : s + 1))}
              style={{
                background: '#0b1c3b',
                border: 'none',
                borderRadius: '50%',
                width: 36,
                height: 36,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <img src="/Paimana_Files/next-icon-1.png" alt="Next" style={{ width: 18, filter: 'invert(1)' }} />
            </button>
          </div>
        </div>

        {/* Cards */}
        <div className="row mx-3" style={{ gap: 0 }}>
          {visible.map((p, i) => (
            <div key={start + i} className="col-lg-3 col-md-6 col-sm-12" style={{ padding: '0 8px 16px' }}>
              <div className="on-gong shadow-sm p-3 mb-5 bg-white rounded" style={{ height: '100%' }}>
                {/* Head */}
                <div className="on-going-head d-flex border-bottom align-items-center extralayer">
                  <div className="on-going-head-img highlyimg">
                    <img
                      src={`/Paimana_Files/${p.imgFile}`}
                      alt={p.sector}
                      className="highlyimg"
                      onError={(e) => (e.currentTarget.style.display = 'none')}
                    />
                  </div>
                  <div className="on-going-head-title py-3 highlyctn">
                    <h5 style={{ color: '#060e37' }}>{p.sector}</h5>
                  </div>
                  <div className="agency-name">
                    <h5>{p.agency}</h5>
                  </div>
                  <div className="project-name">
                    <h6 className="project-short" title={p.name}>
                      {p.name.length > 80 ? p.name.slice(0, 80) + '…' : p.name}
                    </h6>
                  </div>
                </div>

                {/* Stats */}
                <div className="on-going-content">
                  <div className="d-flex py-3 bdrlft">
                    <div className="Cost ml">
                      <p>Original Cost</p>
                      <p><span>(in Cr)</span></p>
                      <h5>{p.originalCost}</h5>
                    </div>
                    <div className="Cost mr" style={{ marginLeft: 28 }}>
                      <p>Physical Progress</p>
                      <p><span>(in %)</span></p>
                      <h5>{p.physicalProgress}</h5>
                    </div>
                  </div>
                  <div className="d-flex py-3 bdrlft">
                    <div className="Cost ml">
                      <p>Latest Revised Cost</p>
                      <p><span>(in Cr)</span></p>
                      <h5>{p.revisedCost}</h5>
                    </div>
                    <div className="Cost mr" style={{ marginLeft: -22 }}>
                      <p>Latest Revised</p>
                      <p><span>Comp. Date</span></p>
                      <h5>{p.completionDate}</h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
