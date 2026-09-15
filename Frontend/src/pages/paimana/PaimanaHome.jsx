import React from 'react';
import { usePaimanaStyles } from '../../hooks/usePaimanaStyles';
import PaimanaHeader from '../../components/paimana/PaimanaHeader';
import PaimanaBanner from '../../components/paimana/PaimanaBanner';
import MinistryWheelSection from '../../components/paimana/MinistryWheelSection';
import StateProjectsSection from '../../components/paimana/StateProjectsSection';
import HighValueProjectsCarousel from '../../components/paimana/HighValueProjectsCarousel';

import AppDownloadSection from '../../components/paimana/AppDownloadSection';
import PaimanaFooter from '../../components/paimana/PaimanaFooter';

/**
 * Native React implementation of the PAIMANA portal.
 * Replaces the previous iframe approach.
 * CSS is injected/removed by usePaimanaStyles to keep PRAHARI styles isolated.
 */
export default function PaimanaHome() {
  usePaimanaStyles();

  return (
    <div id="pagelayout">
      <PaimanaHeader />
      <main id="mainPage">
        <PaimanaBanner />
        <MinistryWheelSection />
        <StateProjectsSection />
        <HighValueProjectsCarousel />

        <AppDownloadSection />
      </main>
      <PaimanaFooter />
    </div>
  );
}
