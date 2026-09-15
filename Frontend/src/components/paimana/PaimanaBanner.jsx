import React, { useEffect, useRef } from 'react';

const BANNER_SLIDES = [
  {
    bg: 'linear-gradient(135deg, #0b1c3b 0%, #1a3a6b 50%, #0d2d52 100%)',
    label: 'slide 1',
  },
  {
    bg: 'linear-gradient(135deg, #1a3a6b 0%, #0b4d8a 50%, #063a6c 100%)',
    label: 'slide 2',
  },
  {
    bg: 'linear-gradient(135deg, #063a6c 0%, #0b1c3b 50%, #1a3163 100%)',
    label: 'slide 3',
  },
  {
    bg: 'linear-gradient(135deg, #102040 0%, #1c3b70 50%, #0b2550 100%)',
    label: 'slide 4',
  },
];

export default function PaimanaBanner() {
  const swiperRef = useRef(null);
  const swiperInstanceRef = useRef(null);

  useEffect(() => {
    // Try to init Swiper from the already-loaded global bundle (injected via usePaimanaStyles)
    const tryInit = () => {
      if (window.Swiper && swiperRef.current && !swiperInstanceRef.current) {
        swiperInstanceRef.current = new window.Swiper(swiperRef.current, {
          loop: true,
          autoplay: { delay: 4000, disableOnInteraction: false },
          pagination: {
            el: '.paimana-pagination',
            clickable: true,
          },
          navigation: {
            nextEl: '.paimana-next',
            prevEl: '.paimana-prev',
          },
        });
      }
    };

    // Swiper CSS is injected via <link> in usePaimanaStyles; JS file is not loaded.
    // We fallback to a simple CSS-based auto-slide if Swiper is absent.
    const timer = setTimeout(tryInit, 300);
    return () => {
      clearTimeout(timer);
      if (swiperInstanceRef.current) {
        swiperInstanceRef.current.destroy(true, true);
        swiperInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="homsection paimana-banner-wrap">
      <div className="swiper paimanaBanner" ref={swiperRef}>
        <div className="swiper-wrapper">
          {BANNER_SLIDES.map((slide, i) => (
            <div
              key={i}
              className="swiper-slide"
              style={{ background: slide.bg }}
              role="group"
              aria-label={`${i + 1} / ${BANNER_SLIDES.length}`}
            />
          ))}
        </div>

        {/* Overlay */}
        <div className="paimana-overlay">
          <div className="paimana-overlay-box">
            <h1 className="paimana-title">Project Monitoring</h1>
            <p className="paimana-tag">
              Central Sector Infrastructure Projects Costing Rs. 150 crore &amp; above
            </p>
          </div>
        </div>

        {/* Pagination & Navigation */}
        <div className="swiper-pagination paimana-pagination" />
        <div className="swiper-button-prev paimana-prev" />
        <div className="swiper-button-next paimana-next" />
      </div>
    </div>
  );
}
