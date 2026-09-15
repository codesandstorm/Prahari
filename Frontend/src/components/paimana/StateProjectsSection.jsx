import React, { useState } from 'react';
import { ALL_STATE_STATS, STATE_STATS } from '../../data/paimanaStaticData';

// Simplified clickable India SVG map — state regions as named <g> elements
// Each state name matches STATE_STATS keys.
// The original map used ArcGIS/Dojo polygon paths; here we use a simple SVG outline.
// State polygons approximate positions (not geographically precise, sufficient for demo).
const STATE_POSITIONS = [
  { name: 'Jammu & Kashmir',    cx: 220, cy: 110 },
  { name: 'Himachal Pradesh',   cx: 260, cy: 155 },
  { name: 'Punjab',             cx: 200, cy: 170 },
  { name: 'Uttarakhand',        cx: 295, cy: 175 },
  { name: 'Haryana',            cx: 230, cy: 200 },
  { name: 'Delhi',              cx: 248, cy: 215 },
  { name: 'Uttar Pradesh',      cx: 320, cy: 225 },
  { name: 'Rajasthan',          cx: 190, cy: 260 },
  { name: 'Madhya Pradesh',     cx: 285, cy: 295 },
  { name: 'Bihar',              cx: 390, cy: 250 },
  { name: 'West Bengal',        cx: 430, cy: 290 },
  { name: 'Jharkhand',          cx: 400, cy: 295 },
  { name: 'Odisha',             cx: 395, cy: 340 },
  { name: 'Chhattisgarh',       cx: 340, cy: 335 },
  { name: 'Gujarat',            cx: 145, cy: 295 },
  { name: 'Maharashtra',        cx: 215, cy: 360 },
  { name: 'Telangana',          cx: 300, cy: 390 },
  { name: 'Andhra Pradesh',     cx: 330, cy: 430 },
  { name: 'Karnataka',          cx: 240, cy: 435 },
  { name: 'Tamil Nadu',         cx: 295, cy: 490 },
  { name: 'Kerala',             cx: 240, cy: 495 },
  { name: 'Goa',                cx: 175, cy: 400 },
  { name: 'Arunachal Pradesh',  cx: 500, cy: 195 },
  { name: 'Assam',              cx: 475, cy: 225 },
  { name: 'Nagaland',           cx: 510, cy: 235 },
  { name: 'Manipur',            cx: 510, cy: 260 },
  { name: 'Mizoram',            cx: 500, cy: 280 },
  { name: 'Meghalaya',          cx: 465, cy: 250 },
  { name: 'Tripura',            cx: 490, cy: 295 },
  { name: 'Sikkim',             cx: 440, cy: 210 },
];

function IndiaMapSvg({ activeState, onStateClick }) {
  return (
    <svg
      viewBox="0 0 620 560"
      style={{ width: '100%', maxHeight: 520, cursor: 'pointer' }}
      aria-label="India Map – click a state label"
    >
      {/* Background */}
      <rect x="0" y="0" width="620" height="560" rx="12" fill="#e8f4f8" />

      {/* Ocean/country outline placeholder */}
      <ellipse cx="310" cy="300" rx="230" ry="270" fill="#c5dce5" opacity="0.4" />

      {/* State dots + labels */}
      {STATE_POSITIONS.map(({ name, cx, cy }) => {
        const hasData = !!STATE_STATS[name];
        const isActive = activeState === name;
        const color = isActive ? '#e74c3c' : hasData ? '#1a3a6b' : '#888';
        return (
          <g
            key={name}
            onClick={() => hasData && onStateClick(name)}
            style={{ cursor: hasData ? 'pointer' : 'default' }}
            aria-label={name}
          >
            <circle
              cx={cx}
              cy={cy}
              r={isActive ? 8 : 5}
              fill={color}
              opacity={0.85}
            />
            <text
              x={cx + 9}
              y={cy + 4}
              fontSize={isActive ? 10 : 9}
              fontWeight={isActive ? '700' : '400'}
              fill={color}
              fontFamily="Montserrat, sans-serif"
            >
              {name}
            </text>
          </g>
        );
      })}

      {/* Tooltip label for active state */}
      {activeState && (
        <rect
          x="5" y="5" width="200" height="24" rx="4"
          fill="#1a3a6b" opacity="0.85"
        />
      )}
      {activeState && (
        <text x="12" y="21" fontSize="11" fill="#fff" fontFamily="Montserrat,sans-serif">
          {activeState}
        </text>
      )}
    </svg>
  );
}

function StatRow({ label, value }) {
  return (
    <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
      <div className="text-center m-0">
        <p className="count-head py-2 d-inline-block">{label}</p>
        <h5><label>{value}</label></h5>
      </div>
    </div>
  );
}

export default function StateProjectsSection() {
  const [activeState, setActiveState] = useState(null);

  const stats = activeState && STATE_STATS[activeState]
    ? STATE_STATS[activeState]
    : ALL_STATE_STATS;

  const displayTitle = activeState || ALL_STATE_STATS.name;

  return (
    <section className="position-relative state-bg">
      <div id="StateView">
        <div className="container-fluid">
          <div className="row mx-5 align-items-center">
            {/* ── Stats panel ── */}
            <div className="col-sm-12 col-md-12 col-xl-6">
              <div className="state-wise-project">
                <h2 className="mt-2">
                  State-wise Projects{' '}
                  <span style={{ fontStyle: 'italic', fontSize: 12 }}>
                    <label id="FreezeDate">(as of July, 2026)</label>
                  </span>
                </h2>
              </div>

              <div className="row tabcontent shadow-lg p-3 bg-body rounded active" id="blk">
                <h3
                  className="text-center py-3 heading brd-btm crd-bg-clr1 text-white"
                  id="statename"
                >
                  {displayTitle}
                </h3>

                <div className="row pt-3 px-3 m-0" id="state-projects-container">
                  <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
                    <img src="/Paimana_Files/project-count.png" id="StatePCImg" alt="Project Count" />
                    <div className="text-center m-0">
                      <p className="count-head py-2 d-inline-block">Project Count <span>(No.) </span></p>
                      <h5><label id="StatePC">{stats.count}</label></h5>
                    </div>
                  </div>

                  <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
                    <img src="/Paimana_Files/orginal-cost.png" id="StateOCImg" alt="Original Cost" />
                    <div className="text-center m-0">
                      <p className="count-head py-2 d-inline-block">Original Cost <span>(in Cr.)</span></p>
                      <h5><label id="StateOC">{stats.originalCost}</label></h5>
                    </div>
                  </div>

                  <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
                    <img src="/Paimana_Files/revised-cost.png" id="StateRCImg" alt="Latest Revised Cost" />
                    <div className="text-center m-0">
                      <p className="count-head py-2 d-inline-block">Latest Revised Cost <span>(in Cr.)</span></p>
                      <h5><label id="StateRC">{stats.revisedCost}</label></h5>
                    </div>
                  </div>

                  <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
                    <img src="/Paimana_Files/expenditure.png" id="StateEXImg" alt="Expenditure" />
                    <div className="text-center m-0">
                      <p className="count-head py-2 d-inline-block">Expenditure(Cumm.) <span>(in Cr.)</span></p>
                      <h5><label id="StateEx">{stats.expenditure}</label></h5>
                    </div>
                  </div>

                  <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
                    <img src="/Paimana_Files/compliance-year.png" id="StateCompImg" alt="Compliance Year" />
                    <div className="text-center m-0">
                      <p className="count-head py-2 d-inline-block">Completed During month <span>(No.)</span></p>
                      <h5><label id="StateComp">{stats.completedMonth}</label></h5>
                    </div>
                  </div>

                  <div className="col-sm-6 d-flex bg-white py-3 stbgcolor">
                    <img src="/Paimana_Files/new-project.png" id="StateNewImg" alt="Newly Added Project" />
                    <div className="text-center m-0">
                      <p className="count-head py-2 d-inline-block">Newly Added <span>(No.)</span></p>
                      <h5><label id="StateNewAdded">{stats.newlyAdded}</label></h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ── Map panel ── */}
            <div className="col-sm-12 col-md-12 col-xl-6">
              <div id="mapDiv" className="map" style={{ minHeight: 420, padding: 10 }}>
                <IndiaMapSvg
                  activeState={activeState}
                  onStateClick={(name) =>
                    setActiveState((prev) => (prev === name ? null : name))
                  }
                />
                <p style={{ textAlign: 'center', color: '#666', fontSize: 12, marginTop: 6 }}>
                  Click a state to view its project statistics
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
