import React from 'react';

export default function AppDownloadSection() {
  return (
    <section className="appdownload">
      <div className="container-fluid">
        <div className="appdownbox">
          <div className="apppaimana">
            <img src="/Paimana_Files/apppaimana.png" alt="App Paimana" />
          </div>
          <div className="appmiddlecontent">
            <h3>Coming Soon</h3>
            <p>Discover your new favorite spaces, Download from Google Play/iOS App.</p>
          </div>
          <div className="appicondownload">
            {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
            <a href="#" onClick={(e) => e.preventDefault()}>
              <img src="/Paimana_Files/playstore-icon.png" alt="Paimana Play Store" />
            </a>
            {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
            <a href="#" onClick={(e) => e.preventDefault()}>
              <img src="/Paimana_Files/apple-store.png" alt="Paimana App Store" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
