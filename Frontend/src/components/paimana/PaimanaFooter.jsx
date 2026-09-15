import React from 'react';
import { Link } from 'react-router-dom';

export default function PaimanaFooter() {
  return (
    <footer>
      <div className="container">
        {/* Brand row */}
        <div className="footer-brand">
          <div className="footer-brand-left">
            <a
              href="https://www.mospi.gov.in/"
              target="_blank"
              rel="noreferrer"
              className="ministry-block"
            >
              <img
                src="/Paimana_Files/logo-mospi.png"
                alt="Ministry of Statistics and Programme Implementation"
                className="footer-ministry-img"
              />
            </a>
            <a
              href="https://www.dic.gov.in/"
              target="_blank"
              rel="noreferrer"
              title="Data for Development"
            >
              <img
                src="/Paimana_Files/data-for-dev.png"
                alt="Data for Development"
                className="footer-partner-img"
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            </a>
          </div>
          <div className="niclogo">
            <div className="negd-credit">
              <p className="negd-credit-title">Design and Developed by NeGD</p>
              <a
                href="https://negd.gov.in/"
                target="_blank"
                rel="noreferrer noopener"
              >
                <img
                  src="/Paimana_Files/negdlogo.png"
                  alt="National e-Governance Division (NeGD)"
                  className="negd-credit-logo"
                />
              </a>
            </div>
          </div>
        </div>

        {/* Contact */}
        <div className="footertop">
          <div className="contactbox">
            <h4>Get in touch</h4>
            <h3>
              Ministry of Statistics and Programme Implementation, Government of India,
              Khurshid Lal Bhawan, Janpath, New Delhi-110001 (India).
            </h3>
            <ul className="contactlist">
              <li>
                <a href="tel:01123455604">
                  <img src="/Paimana_Files/tel-icon.png" alt="" />{' '}
                  011-23455604
                </a>
              </li>
              <li>
                <a href="mailto:dir-ipmd@mospi.gov.in">
                  <img src="/Paimana_Files/email-icon.png" alt="" />{' '}
                  dir-ipmd[at]mospi[dot]gov[dot]in
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Quick Links */}
        <div className="footermiddle">
          <div className="fmiddlecnt">
            <h4>Quick Links</h4>
            <ul>
              <li><Link to="/">Home</Link></li>
              <li>
                <a
                  href="https://paimana-proj.mospi.gov.in/ContactUs/Contact"
                  target="_blank"
                  rel="noreferrer"
                >
                  Contact Us
                </a>
              </li>
              <li>
                <a
                  href="https://paimana-proj.mospi.gov.in/FAQ"
                  target="_blank"
                  rel="noreferrer"
                >
                  FAQs
                </a>
              </li>
              <li>
                <a
                  href="https://paimana-proj.mospi.gov.in/QuickLink/SiteMap"
                  target="_blank"
                  rel="noreferrer"
                >
                  Site Map
                </a>
              </li>
              <li>
                <a
                  href="https://paimana-proj.mospi.gov.in/QuickLink/HyperLinkPolicy"
                  target="_blank"
                  rel="noreferrer"
                >
                  Hyperlinking Policy
                </a>
              </li>
              <li>
                <a
                  href="https://paimana-proj.mospi.gov.in/QuickLink/PrivacyPolicy"
                  target="_blank"
                  rel="noreferrer"
                >
                  Privacy Policy
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="footerbottom">
        <div className="container">
          <p>
            <b>Content owned and maintained by:</b> Infrastructure &amp; Project Monitoring
            Division (IPMD) | Ministry of Statistics and Programme Implementation.
          </p>
          <p className="mb-0">
            Copyright &copy; 2025 Ministry of Statistics and Programme Implementation
          </p>
        </div>
      </div>
    </footer>
  );
}
