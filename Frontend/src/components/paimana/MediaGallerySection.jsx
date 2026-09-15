import React, { useState } from 'react';
import { GALLERY_IMAGES } from '../../data/paimanaStaticData';

const VISIBLE = 3;

export default function MediaGallerySection() {
  const [start, setStart] = useState(0);

  const canPrev = start > 0;
  const canNext = start + VISIBLE < GALLERY_IMAGES.length;
  const visible = GALLERY_IMAGES.slice(start, start + VISIBLE);

  return (
    <div
      id="medialist"
      style={{ padding: '30px 0', background: '#fff' }}
    >
      <div className="container-fluid">
        <div className="row mb-3 align-items-center mx-3">
          <div className="col">
            <h2 style={{ fontWeight: 700, color: '#0b1c3b', fontSize: 22 }}>Media Gallery</h2>
          </div>
          <div className="col-auto" style={{ display: 'flex', gap: 8 }}>
            <button
              aria-label="Previous"
              disabled={!canPrev}
              onClick={() => setStart((s) => Math.max(0, s - 1))}
              style={{ background: 'none', border: 'none', cursor: canPrev ? 'pointer' : 'default', opacity: canPrev ? 1 : 0.3 }}
            >
              <img src="/Paimana_Files/prev-icon-1.png" alt="Prev" style={{ width: 24 }} />
            </button>
            <button
              aria-label="Next"
              disabled={!canNext}
              onClick={() => setStart((s) => s + 1)}
              style={{ background: 'none', border: 'none', cursor: canNext ? 'pointer' : 'default', opacity: canNext ? 1 : 0.3 }}
            >
              <img src="/Paimana_Files/next-icon-1.png" alt="Next" style={{ width: 24 }} />
            </button>
          </div>
        </div>
        <div className="row mx-3">
          {visible.map((file) => (
            <div key={file} className="col-md-4 col-sm-12" style={{ padding: '0 8px 16px' }}>
              <img
                src={`/Paimana_Files/${file}`}
                alt="Gallery"
                style={{
                  width: '100%',
                  aspectRatio: '16/9',
                  objectFit: 'cover',
                  borderRadius: 8,
                  boxShadow: '0 2px 8px rgba(0,0,0,.12)',
                }}
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
