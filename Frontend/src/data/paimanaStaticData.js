/**
 * PAIMANA Static Data
 * All demo data extracted from paimana-original.html.
 * Replace with API calls when backend is ready.
 */

// ── Ministry-wise data ────────────────────────────────────────────────────────
export const MINISTRIES = [
  { id: 38, shortName: 'MoM',        imgFile: 'Ministry-of-Mines-India.png',                          fullName: 'Ministry of Mines', stats: { count: 42, originalCost: '₹ 62,345.12', revisedCost: '₹ 71,230.45', expenditure: '₹ 28,910.33', completedMonth: 1, newlyAdded: 0 } },
  { id: 29, shortName: 'DPIIT',      imgFile: 'dpiit.png',                                            fullName: 'Department for Promotion of Industry and Internal Trade', stats: { count: 15, originalCost: '₹ 18,200.00', revisedCost: '₹ 19,450.00', expenditure: '₹ 9,100.50', completedMonth: 0, newlyAdded: 0 } },
  { id: 33, shortName: 'MoHFW',      imgFile: 'Ministry-of-Health-and-Family-Welfare.png',            fullName: 'Ministry of Health and Family Welfare', stats: { count: 88, originalCost: '₹ 42,100.00', revisedCost: '₹ 44,550.00', expenditure: '₹ 21,080.00', completedMonth: 2, newlyAdded: 1 } },
  { id: 30, shortName: 'DWR, RD & GR', imgFile: 'Department-of-Water-Resources-River-Development-and-GR.png', fullName: 'Department of Water Resources, River Development & GR', stats: { count: 74, originalCost: '₹ 2,15,400.00', revisedCost: '₹ 2,82,100.00', expenditure: '₹ 1,04,300.00', completedMonth: 0, newlyAdded: 2 } },
  { id: 22, shortName: 'MoHUA',      imgFile: 'Ministry-of-Housing-and-Urban-Affairs.png',           fullName: 'Ministry of Housing and Urban Affairs', stats: { count: 120, originalCost: '₹ 1,84,700.00', revisedCost: '₹ 2,10,350.00', expenditure: '₹ 95,600.00', completedMonth: 3, newlyAdded: 0 } },
  { id: 2,  shortName: 'MoRTH',      imgFile: 'Ministry-of-Road-Transport-and-Highways.png',         fullName: 'Ministry of Road Transport and Highways', stats: { count: 382, originalCost: '₹ 8,52,300.00', revisedCost: '₹ 9,41,000.00', expenditure: '₹ 4,23,500.00', completedMonth: 5, newlyAdded: 4 } },
  { id: 5,  shortName: 'DHE',        imgFile: 'Department-of-Higher-Education.png',                  fullName: 'Department of Higher Education', stats: { count: 30, originalCost: '₹ 15,165.68', revisedCost: '₹ 14,973.27', expenditure: '₹ 8,632.49', completedMonth: 0, newlyAdded: 0 } },
  { id: 1,  shortName: 'MoR',        imgFile: 'Ministry-of-Railways.png',                            fullName: 'Ministry of Railways', stats: { count: 274, originalCost: '₹ 5,32,800.00', revisedCost: '₹ 6,18,400.00', expenditure: '₹ 2,87,200.00', completedMonth: 4, newlyAdded: 3 } },
  { id: 12, shortName: 'MoPSW',      imgFile: 'Ministry-of-Ports-Shipping-and-Waterways.png',        fullName: 'Ministry of Ports, Shipping and Waterways', stats: { count: 56, originalCost: '₹ 78,200.00', revisedCost: '₹ 84,100.00', expenditure: '₹ 38,400.00', completedMonth: 1, newlyAdded: 0 } },
  { id: 49, shortName: 'MoLE',       imgFile: 'Ministry-of-Labour-and-Employment.png',               fullName: 'Ministry of Labour and Employment', stats: { count: 12, originalCost: '₹ 8,400.00', revisedCost: '₹ 9,100.00', expenditure: '₹ 4,200.00', completedMonth: 0, newlyAdded: 0 } },
  { id: 35, shortName: 'MoC',        imgFile: 'Coal-India.png',                                      fullName: 'Ministry of Coal', stats: { count: 48, originalCost: '₹ 1,24,500.00', revisedCost: '₹ 1,38,200.00', expenditure: '₹ 52,300.00', completedMonth: 0, newlyAdded: 1 } },
  { id: 32, shortName: 'DoT',        imgFile: 'Department-of-Telecommunications.png',                fullName: 'Department of Telecommunications', stats: { count: 31, originalCost: '₹ 2,07,194.71', revisedCost: '₹ 1,33,825.11', expenditure: '₹ 1,02,879.15', completedMonth: 0, newlyAdded: 0 } },
  { id: 10, shortName: 'MoPNG',      imgFile: 'Ministry-of-Petroleum-and-Natural-Gas.png',           fullName: 'Ministry of Petroleum and Natural Gas', stats: { count: 64, originalCost: '₹ 3,02,100.00', revisedCost: '₹ 3,54,800.00', expenditure: '₹ 1,64,200.00', completedMonth: 2, newlyAdded: 0 } },
  { id: 20, shortName: 'DoS',        imgFile: 'Department-of-Sports.png',                            fullName: 'Department of Sports', stats: { count: 18, originalCost: '₹ 12,400.00', revisedCost: '₹ 14,100.00', expenditure: '₹ 6,800.00', completedMonth: 0, newlyAdded: 0 } },
  { id: 14, shortName: 'MoS',        imgFile: 'Ministry-of-Steel.png',                               fullName: 'Ministry of Steel', stats: { count: 22, originalCost: '₹ 68,200.00', revisedCost: '₹ 74,500.00', expenditure: '₹ 32,100.00', completedMonth: 1, newlyAdded: 0 } },
  { id: 3,  shortName: 'MoCA',       imgFile: 'Ministry-of-Civil-Aviation-India.png',                fullName: 'Ministry of Civil Aviation', stats: { count: 45, originalCost: '₹ 84,300.00', revisedCost: '₹ 92,100.00', expenditure: '₹ 41,500.00', completedMonth: 2, newlyAdded: 1 } },
  { id: 15, shortName: 'MoP',        imgFile: 'Ministry-of-Power.png',                               fullName: 'Ministry of Power', stats: { count: 136, originalCost: '₹ 4,21,500.00', revisedCost: '₹ 4,87,200.00', expenditure: '₹ 2,14,600.00', completedMonth: 3, newlyAdded: 2 } },
  { id: 0,  shortName: 'All',        imgFile: 'new_image.png',                                       fullName: 'All Ministries & Departments', stats: { count: 1775, originalCost: '₹ 33,70,138.22', revisedCost: '₹ 37,10,641.55', expenditure: '₹ 19,26,099.57', completedMonth: 0, newlyAdded: 0 } },
];

// ── Sector-wise data ──────────────────────────────────────────────────────────
export const SECTORS = [
  { id: 107, shortName: 'Roads & Highways',         imgFile: 'RoadsHighways.png',           stats: { count: 382, originalCost: '₹ 8,52,300.00', revisedCost: '₹ 9,41,000.00', expenditure: '₹ 4,23,500.00', completedMonth: 5, newlyAdded: 4 } },
  { id: 108, shortName: 'Railways',                 imgFile: 'Railways.png',                stats: { count: 274, originalCost: '₹ 5,32,800.00', revisedCost: '₹ 6,18,400.00', expenditure: '₹ 2,87,200.00', completedMonth: 4, newlyAdded: 3 } },
  { id: 123, shortName: 'Coal',                     imgFile: 'Coal.svg',                    stats: { count: 48, originalCost: '₹ 1,24,500.00', revisedCost: '₹ 1,38,200.00', expenditure: '₹ 52,300.00', completedMonth: 0, newlyAdded: 1 } },
  { id: 12,  shortName: 'Oil & Gas',                imgFile: 'OilGas.png',                  stats: { count: 64, originalCost: '₹ 3,02,100.00', revisedCost: '₹ 3,54,800.00', expenditure: '₹ 1,64,200.00', completedMonth: 2, newlyAdded: 0 } },
  { id: 2,   shortName: 'ALL',                      imgFile: 'All.svg',                     stats: { count: 1775, originalCost: '₹ 33,70,138.22', revisedCost: '₹ 37,10,641.55', expenditure: '₹ 19,26,099.57', completedMonth: 0, newlyAdded: 0 } },
  { id: 102, shortName: 'Transmission & Distribution', imgFile: 'TransmissionDistribution.svg', stats: { count: 136, originalCost: '₹ 4,21,500.00', revisedCost: '₹ 4,87,200.00', expenditure: '₹ 2,14,600.00', completedMonth: 3, newlyAdded: 2 } },
  { id: 113, shortName: 'Healthcare',               imgFile: 'Healthcare.png',              stats: { count: 88, originalCost: '₹ 42,100.00', revisedCost: '₹ 44,550.00', expenditure: '₹ 21,080.00', completedMonth: 2, newlyAdded: 1 } },
  { id: 3,   shortName: 'Electricity Generation',   imgFile: 'ElectricityGeneration.png',   stats: { count: 120, originalCost: '₹ 1,84,700.00', revisedCost: '₹ 2,10,350.00', expenditure: '₹ 95,600.00', completedMonth: 3, newlyAdded: 0 } },
  { id: 30,  shortName: 'Telecommunication',        imgFile: 'Telecommunication.png',       stats: { count: 31, originalCost: '₹ 2,07,194.71', revisedCost: '₹ 1,33,825.11', expenditure: '₹ 1,02,879.15', completedMonth: 0, newlyAdded: 0 } },
  { id: 31,  shortName: 'Education',                imgFile: 'Education.png',               stats: { count: 42, originalCost: '₹ 35,400.00', revisedCost: '₹ 38,200.00', expenditure: '₹ 17,600.00', completedMonth: 1, newlyAdded: 0 } },
  { id: 111, shortName: 'Urban Public Transport',   imgFile: 'UrbanPublicTransport.svg',    stats: { count: 56, originalCost: '₹ 1,24,300.00', revisedCost: '₹ 1,38,700.00', expenditure: '₹ 62,100.00', completedMonth: 2, newlyAdded: 1 } },
];

// ── State-wise aggregate (all states) ─────────────────────────────────────────
export const ALL_STATE_STATS = {
  name: 'All State Details',
  count: 1775,
  originalCost: '₹ 33,70,138.22',
  revisedCost: '₹ 37,10,641.55',
  expenditure: '₹ 19,26,099.57',
  completedMonth: 0,
  newlyAdded: 0,
};

// Individual states (subset – expand when real API available)
export const STATE_STATS = {
  'Andhra Pradesh':    { count: 82,  originalCost: '₹ 1,24,300', revisedCost: '₹ 1,38,200', expenditure: '₹ 62,400', completedMonth: 1, newlyAdded: 0 },
  'Arunachal Pradesh': { count: 28,  originalCost: '₹ 48,200',   revisedCost: '₹ 52,100',   expenditure: '₹ 22,100', completedMonth: 0, newlyAdded: 1 },
  'Assam':             { count: 44,  originalCost: '₹ 68,400',   revisedCost: '₹ 74,200',   expenditure: '₹ 32,100', completedMonth: 0, newlyAdded: 0 },
  'Bihar':             { count: 61,  originalCost: '₹ 92,100',   revisedCost: '₹ 1,02,400', expenditure: '₹ 46,200', completedMonth: 1, newlyAdded: 2 },
  'Chhattisgarh':      { count: 35,  originalCost: '₹ 52,400',   revisedCost: '₹ 58,100',   expenditure: '₹ 24,300', completedMonth: 0, newlyAdded: 0 },
  'Goa':               { count: 14,  originalCost: '₹ 18,200',   revisedCost: '₹ 19,800',   expenditure: '₹ 9,400',  completedMonth: 0, newlyAdded: 0 },
  'Gujarat':           { count: 96,  originalCost: '₹ 1,82,400', revisedCost: '₹ 2,04,100', expenditure: '₹ 92,300', completedMonth: 2, newlyAdded: 1 },
  'Haryana':           { count: 48,  originalCost: '₹ 72,300',   revisedCost: '₹ 81,200',   expenditure: '₹ 38,100', completedMonth: 1, newlyAdded: 0 },
  'Himachal Pradesh':  { count: 32,  originalCost: '₹ 46,200',   revisedCost: '₹ 51,300',   expenditure: '₹ 22,400', completedMonth: 0, newlyAdded: 1 },
  'Jharkhand':         { count: 38,  originalCost: '₹ 58,100',   revisedCost: '₹ 64,300',   expenditure: '₹ 28,200', completedMonth: 0, newlyAdded: 0 },
  'Karnataka':         { count: 86,  originalCost: '₹ 1,48,200', revisedCost: '₹ 1,64,300', expenditure: '₹ 74,100', completedMonth: 2, newlyAdded: 1 },
  'Kerala':            { count: 54,  originalCost: '₹ 84,300',   revisedCost: '₹ 92,100',   expenditure: '₹ 42,200', completedMonth: 1, newlyAdded: 0 },
  'Madhya Pradesh':    { count: 72,  originalCost: '₹ 1,12,400', revisedCost: '₹ 1,24,300', expenditure: '₹ 56,100', completedMonth: 1, newlyAdded: 2 },
  'Maharashtra':       { count: 124, originalCost: '₹ 2,42,300', revisedCost: '₹ 2,68,400', expenditure: '₹ 1,24,300', completedMonth: 3, newlyAdded: 2 },
  'Manipur':           { count: 18,  originalCost: '₹ 28,400',   revisedCost: '₹ 31,200',   expenditure: '₹ 14,100', completedMonth: 0, newlyAdded: 0 },
  'Meghalaya':         { count: 16,  originalCost: '₹ 24,200',   revisedCost: '₹ 26,800',   expenditure: '₹ 12,400', completedMonth: 0, newlyAdded: 0 },
  'Mizoram':           { count: 12,  originalCost: '₹ 18,400',   revisedCost: '₹ 20,100',   expenditure: '₹ 9,200',  completedMonth: 0, newlyAdded: 0 },
  'Nagaland':          { count: 14,  originalCost: '₹ 22,100',   revisedCost: '₹ 24,300',   expenditure: '₹ 11,200', completedMonth: 0, newlyAdded: 0 },
  'Odisha':            { count: 58,  originalCost: '₹ 92,400',   revisedCost: '₹ 1,02,100', expenditure: '₹ 46,800', completedMonth: 1, newlyAdded: 1 },
  'Punjab':            { count: 42,  originalCost: '₹ 64,300',   revisedCost: '₹ 71,200',   expenditure: '₹ 32,400', completedMonth: 1, newlyAdded: 0 },
  'Rajasthan':         { count: 76,  originalCost: '₹ 1,18,200', revisedCost: '₹ 1,32,400', expenditure: '₹ 59,300', completedMonth: 1, newlyAdded: 2 },
  'Sikkim':            { count: 10,  originalCost: '₹ 14,200',   revisedCost: '₹ 15,800',   expenditure: '₹ 7,100',  completedMonth: 0, newlyAdded: 0 },
  'Tamil Nadu':        { count: 94,  originalCost: '₹ 1,62,400', revisedCost: '₹ 1,81,200', expenditure: '₹ 82,300', completedMonth: 2, newlyAdded: 1 },
  'Telangana':         { count: 64,  originalCost: '₹ 1,02,300', revisedCost: '₹ 1,14,200', expenditure: '₹ 52,400', completedMonth: 1, newlyAdded: 0 },
  'Tripura':           { count: 14,  originalCost: '₹ 22,300',   revisedCost: '₹ 24,800',   expenditure: '₹ 11,400', completedMonth: 0, newlyAdded: 0 },
  'Uttar Pradesh':     { count: 136, originalCost: '₹ 2,82,400', revisedCost: '₹ 3,12,300', expenditure: '₹ 1,42,100', completedMonth: 3, newlyAdded: 3 },
  'Uttarakhand':       { count: 32,  originalCost: '₹ 48,300',   revisedCost: '₹ 53,200',   expenditure: '₹ 24,100', completedMonth: 0, newlyAdded: 1 },
  'West Bengal':       { count: 68,  originalCost: '₹ 1,08,400', revisedCost: '₹ 1,21,300', expenditure: '₹ 54,200', completedMonth: 1, newlyAdded: 2 },
};

// ── High-Value Projects (carousel cards) ─────────────────────────────────────
export const HIGH_VALUE_PROJECTS = [
  { sector: 'Railways',        imgFile: 'Railways.png',                    agency: 'National High Speed Rail Corporation [NHSRC]',        name: 'Mumbai-Ahmedabad High Speed Rail Project- 508 km',                                                                 originalCost: '₹ 1,08,000', physicalProgress: '62', revisedCost: '₹ 1,08,000', completionDate: '31/12/2029' },
  { sector: 'Urban Public Transport', imgFile: 'UrbanPublicTransport.svg', agency: 'Chennai Metro Rail Limited [CMRL]',                   name: 'Chennai Metro Rail Phase-II Development Project',                                                                   originalCost: '₹ 63,246',  physicalProgress: '56', revisedCost: '₹ 63,246',  completionDate: '31/08/2029' },
  { sector: 'Telecommunication', imgFile: 'Telecommunication.png',         agency: 'Department of Telecommunications [DoT]',              name: 'BharatNet',                                                                                                         originalCost: '₹ 61,109',  physicalProgress: '100', revisedCost: '₹ 12,709',  completionDate: '31/12/2025' },
  { sector: 'Oil & Gas',        imgFile: 'OilGas.png',                     agency: 'Bharat Petroleum Corporation Limited [BPCL]',         name: 'Ethylene Cracker Project at Bina Refinery including downstream Petrochemical Plants and expansion of Refinery',    originalCost: '₹ 43,367',  physicalProgress: '34', revisedCost: '₹ 43,367',  completionDate: '31/05/2028' },
  { sector: 'Electricity Generation', imgFile: 'ElectricityGeneration.png', agency: 'National Thermal Power Corporation [NTPC]',         name: 'Meja Thermal Power Project, Stage-II , (3x800 MW)',                                                                originalCost: '₹ 38,358',  physicalProgress: '0',  revisedCost: '₹ 38,358',  completionDate: '31/12/2032' },
  { sector: 'Real Estate',       imgFile: 'RealEstate.png',                agency: 'National Buildings Construction Corporation [NBCC]',  name: 'Redevelopment of Seven General Pool Residential Accommodation [GPRA] Colonies in Delhi',                           originalCost: '₹ 32,850',  physicalProgress: '47', revisedCost: '₹ 32,841',  completionDate: '31/12/2025' },
  { sector: 'Coal',              imgFile: 'Coal.svg',                      agency: 'NCL - CIL',                                          name: 'JAYANT EXPN. [20 TO 38 MTPA]',                                                                                     originalCost: '₹ 25,560',  physicalProgress: '2',  revisedCost: '₹ 25,560',  completionDate: '31/03/2032' },
  { sector: 'Transmission & Distribution', imgFile: 'TransmissionDistribution.svg', agency: 'Adani Transmission Limited',              name: 'RAJASTHAN PART I POWER TRANSMISSION LIMITED',                                                                      originalCost: '₹ 25,000',  physicalProgress: '10', revisedCost: '₹ 25,000',  completionDate: '31/12/2027' },
  { sector: 'Roads & Highways',  imgFile: 'RoadsHighways.png',             agency: 'National Highways Authority of India [NHAI]',        name: 'Delhi-Mumbai Expressway',                                                                                          originalCost: '₹ 98,000',  physicalProgress: '78', revisedCost: '₹ 1,02,400', completionDate: '31/03/2027' },
  { sector: 'Healthcare',        imgFile: 'Healthcare.png',                agency: 'AIIMS Delhi',                                        name: 'Expansion and Up-gradation of AIIMS New Delhi',                                                                    originalCost: '₹ 8,200',   physicalProgress: '55', revisedCost: '₹ 9,100',   completionDate: '31/06/2026' },
  { sector: 'Logistics Infrastructure', imgFile: 'LogisticsInfrastructure.svg', agency: 'NICDC',                                       name: 'Integrated Multi Modal Logistics Hub at Nangal Chaudhary in Haryana - Other Trunk Infrastructure Development Phase 1', originalCost: '₹ 763',      physicalProgress: '60', revisedCost: '₹ 763',     completionDate: '15/05/2028' },
  { sector: 'Waste & Water',     imgFile: 'WasteWater.svg',                agency: 'National Mission for Clean Ganga',                   name: 'Interception & Diversion with Rehabilitation of sewerage scheme at Agra under Hybrid annuity based PPP model-Namami Gange Programme', originalCost: '₹ 842', physicalProgress: '84', revisedCost: '₹ 842', completionDate: '31/12/2026' },
  { sector: 'Education',         imgFile: 'Education.png',                 agency: 'INDIAN INSTITUTE OF TECHNOLOGY PALAKKAD',            name: 'Phase B of Construction of Permanent Campus of IIT Palakkad',                                                      originalCost: '₹ 1,527',   physicalProgress: '0',  revisedCost: '₹ 1,527',   completionDate: '31/10/2028' },
  { sector: 'Aviation & Aviation Infrastructure', imgFile: 'AviationAviationInfrastructure.png', agency: 'Airport Authority of India [AAI]', name: 'Development of Lal Bahadur Shastri International airport, Varanasi including C/o New Terminal Building, Apron Extension, Runway Extension, PTT and allied works.', originalCost: '₹ 2,870', physicalProgress: '33', revisedCost: '₹ 2,870', completionDate: '20/07/2027' },
  { sector: 'Metals & Mining',   imgFile: 'MetalsMining.svg',              agency: 'National Mineral Development Corporation Limited [NMDC]', name: 'NMDC Slurry Pipeline Project Phase-1',                                                                        originalCost: '₹ 2,907',   physicalProgress: '96', revisedCost: '₹ 5,427',   completionDate: '15/08/2026' },
];

// ── Gallery images ────────────────────────────────────────────────────────────
export const GALLERY_IMAGES = [
  'gal_638992556274935860.jpeg',
  'gal_638992556318558962.jpeg',
  'gal_638992556363850955.jpeg',
  'gal_638992556404577295.jpeg',
  'gal_638992556454373683.jpeg',
  'gal_638992556493481692.jpeg',
];

// ── Government partner logos ──────────────────────────────────────────────────
export const GOVT_LOGOS = [
  { file: 'swatch Bharat Mission_638984721536825005.jpg', alt: 'Swachh Bharat Mission',    href: 'https://swachhbharatmission.ddws.gov.in/' },
  { file: 'Skill India Digital.png',                      alt: 'Skill India Digital',       href: 'https://www.skillindiadigital.gov.in/home' },
  { file: 'Digital India.png',                            alt: 'Digital India',             href: 'https://csc.gov.in/digitalIndia' },
  { file: 'DPE.png',                                      alt: 'DPE',                       href: 'https://dpe.gov.in/' },
  { file: 'Niti Aayog.png',                               alt: 'Niti Aayog',               href: 'https://www.niti.gov.in/' },
  { file: 'PMG DPIIT.png',                                alt: 'PMG DPIIT',                href: 'https://pmg.dpiit.gov.in/' },
  { file: 'NIC.png',                                      alt: 'NIC',                      href: 'https://www.nic.in/' },
  { file: 'Invest india.png',                             alt: 'Invest India',             href: 'https://www.investindia.gov.in/' },
  { file: 'MY GOV.png',                                   alt: 'MY GOV',                   href: 'https://www.mygov.in/' },
  { file: 'RTI_639035551953175859.png',                   alt: 'RTI Online',               href: 'https://rtionline.gov.in/' },
];
