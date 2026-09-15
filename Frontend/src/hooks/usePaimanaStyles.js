import { useEffect } from 'react';

const PAIMANA_CSS_FILES = [
  '/Paimana_Files/font-awesome.min.css',
  '/Paimana_Files/bootstrap.min.css',
  '/Paimana_Files/family=Montserrat.css',
  '/Paimana_Files/Style.css',
  '/Paimana_Files/about.css',
  '/Paimana_Files/swiper-bundle.min.css',
  '/Paimana_Files/responsive.css',
  '/Paimana_Files/wheel-home.css',
];

/**
 * Injects PAIMANA CSS into <head> on mount and removes it on unmount.
 * Also toggles the body class `paimana-active`.
 */
export function usePaimanaStyles() {
  useEffect(() => {
    const links = PAIMANA_CSS_FILES.map((href) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.setAttribute('data-paimana', 'true');
      document.head.appendChild(link);
      return link;
    });

    document.body.classList.add('paimana-active');

    return () => {
      links.forEach((link) => {
        if (document.head.contains(link)) document.head.removeChild(link);
      });
      document.body.classList.remove('paimana-active');
    };
  }, []);
}
