import React, { useState } from 'react';
import { GOVT_LOGOS } from '../../data/paimanaStaticData';

const VISIBLE = 5;

export default function GovtLogosCarousel() {
  const [start, setStart] = useState(0);
  const canPrev = start > 0;
  const canNext = start + VISIBLE < GOVT_LOGOS.length;
  const visible = GOVT_LOGOS.slice(start, start + VISIBLE);

  return (
    <div
      id="clientlist"
      style={{ background: '#f4f6fa', padding: '24px 0' }}
    >
      <div className="container-fluid">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <button
            aria-label="Previous"
            disabled={!canPrev}
            onClick={() => setStart((s) => Math.max(0, s - 1))}
            style={{ background: 'none', border: 'none', cursor: canPrev ? 'pointer' : 'default', opacity: canPrev ? 1 : 0.3 }}
          >
            <img src="/Paimana_Files/prev-icon-1.png" alt="Prev" style={{ width: 20 }} />
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap', justifyContent: 'center' }}>
            {visible.map((logo) => (
              <a
                key={logo.file}
                href={logo.href}
                target="_blank"
                rel="noreferrer"
                title={logo.alt}
              >
                <img
                  src={`/Paimana_Files/${logo.file}`}
                  alt={logo.alt}
                  style={{ height: 50, objectFit: 'contain', opacity: 0.85, transition: 'opacity .2s' }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.85')}
                  onError={(e) => (e.currentTarget.style.display = 'none')}
                />
              </a>
            ))}
          </div>

          <button
            aria-label="Next"
            disabled={!canNext}
            onClick={() => setStart((s) => s + 1)}
            style={{ background: 'none', border: 'none', cursor: canNext ? 'pointer' : 'default', opacity: canNext ? 1 : 0.3 }}
          >
            <img src="/Paimana_Files/next-icon-1.png" alt="Next" style={{ width: 20 }} />
          </button>
        </div>
      </div>
    </div>
  );
}
