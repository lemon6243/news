import { Article } from '../types';

export const INITIAL_ARTICLES: Article[] = [
  {
    id: 'art-1',
    title: 'Global Renewable Capacity Surpasses 4,000 GW as Solar Deployment Hits Record Velocity',
    summary: 'International Energy Agency reports unprecedented acceleration in distributed photovoltaic installations and offshore wind connections across four continents.',
    content: `A milestone in the global clean energy transition was reached this week as the International Energy Agency confirmed total worldwide installed renewable capacity has formally crossed 4,000 gigawatts. The historic pace was propelled by a 68% year-over-year surge in distributed commercial and residential photovoltaic arrays, coupled with deep infrastructure investments across the European North Sea grid and high-voltage direct current (HVDC) corridors in East Asia.

Grid modernization authorities emphasized that the primary operational bottleneck is now transmission integration rather than generation economics. Major utility consortiums are rapidly deploying grid-forming inverters and modular stationary lithium-iron-phosphate (LFP) storage systems to ensure frequency stability as thermal coal generation retires ahead of statutory deadlines.

"We have exited the phase where renewable parity was debated," stated Dr. Elena Rostova, lead energy economist at the Energy Transitions Forum. "The engineering focus has decisively shifted toward real-time grid orchestration, long-duration energy storage, and cross-border interconnectors that smooth diurnal and meteorological variations."

Financial analysts note that project financing costs for Tier-1 solar utility assets have dropped by 18% over the past eighteen months, despite higher benchmark interest rates, reflecting lenders' increasing confidence in operational longevity and predictive maintenance systems powered by machine vision aerial inspections.`,
    source: {
      name: 'Global Energy Review',
      url: 'https://iea.org',
    },
    author: 'Julian Vance',
    publishedAt: '2026-09-18T18:45:00Z',
    category: 'science',
    readTimeMinutes: 4,
    imageUrl: 'https://images.unsplash.com/photo-1509391365360-2e959784a276?auto=format&fit=crop&w=1200&q=80',
    isBreaking: true,
    trendingRank: 1,
    likesCount: 342,
    commentsCount: 56,
  },
  {
    id: 'art-2',
    title: 'Next-Generation Neural Architecture Cuts Edge Inference Latency by 70% with Zero Accuracy Loss',
    summary: 'Computer scientists unveil sparse mixture-of-quants mechanism allowing high-fidelity language models to run locally on ultra-low-power consumer microcontrollers.',
    content: `Researchers in applied neural engineering have demonstrated a breakthrough quantization pipeline dubbed "Dynamic Sparse Quantization" (DSQ). By dynamically varying weight bit-depth down to 2.4 bits per parameter across non-critical attention heads while maintaining 8-bit precision on key sensory projections, the model preserves 99.8% of base MMLU benchmarks while reducing memory bandwidth contention by nearly three-quarters.

The implications for mobile devices, ambient biomedical telemetry, and autonomous robotics are immense. Rather than routing inference queries through remote cloud clusters—introducing network latency and data governance complexities—embedded edge chips can process complex multimodal sensor streams directly on silicon drawing under 2.5 watts.

"The computational overhead of transformer models had begun to plateau against thermodynamic and battery constraints," remarked co-author Marcus Chen. "By restructuring how activations are routed through sub-networks during runtime, we unlock sub-10 millisecond token generation on hardware previously considered incapable of hosting modern foundational models."

Commercial hardware manufacturers have already begun testing the architecture with early developer toolkits scheduled for general availability next quarter.`,
    source: {
      name: 'Applied Computing Journal',
      url: 'https://techreview.com',
    },
    author: 'Sophia Zhang',
    publishedAt: '2026-09-18T17:15:00Z',
    category: 'technology',
    readTimeMinutes: 5,
    imageUrl: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 2,
    likesCount: 528,
    commentsCount: 89,
  },
  {
    id: 'art-3',
    title: 'Central Banks Harmonize Cross-Border Settlement Protocols for Instant Wholesale Transfers',
    summary: 'A coalition of twelve major central banks finalizes interoperability standards for multi-currency wholesale digital ledgers, reducing settlement delays from days to seconds.',
    content: `In a landmark collaborative development, regulatory authorities and central banking institutions spanning Tokyo, London, Singapore, and Frankfurt ratified the Project Apex framework. The architecture establishes a unified messaging standard and cryptographic guarantee mechanism for atomic settlement of foreign exchange transactions.

Currently, international wholesale payments rely on fragmented correspondent banking tiers, often requiring two to three business days and exposing financial counterparties to overnight foreign exchange volatility and settlement risk. Under the new protocol, liquidity is verified and settled instantaneously against central bank reserves.

Treasury departments at multinational corporations have expressed strong support for the rollout, estimating that reduced collateral locking requirements could free up an estimated $84 billion in global working capital.

Pilot testing will commence in mid-November with twenty-four global custodian banks participating in simulated cross-border sovereign bond repurchasing operations.`,
    source: {
      name: 'Financial Chronicle',
      url: 'https://ft.com',
    },
    author: 'David Sterling',
    publishedAt: '2026-09-18T15:30:00Z',
    category: 'business',
    readTimeMinutes: 4,
    imageUrl: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 3,
    likesCount: 215,
    commentsCount: 34,
  },
  {
    id: 'art-4',
    title: 'Deep-Ocean Autonomous Gliders Map Uncharted Abyssal Ecosystems in the South Pacific',
    summary: 'Fleet of robotic gliders operating at depths exceeding 6,000 meters discovers over forty novel benthic species and hydrothermal microbial communities.',
    content: `An oceanographic consortium utilizing autonomous buoyancy-driven submersibles has returned high-definition bathymetric and ecological datasets from the Tonga and Kermadec trenches. Traversing abyssal plains that have remained largely unexamined since exploratory dredging voyages in the 1960s, the mission cataloged biological specimens displaying unique bioluminescent wavelengths and chemoautotrophic metabolic cycles.

The robotic gliders, equipped with titanium pressure hulls and low-light sensory matrices, completed 140 uninterrupted dive cycles over six months, transmitting acoustic telemetry bursts to relay buoys during brief surface intervals.

Marine biologists point out that these abyssal organisms provide critical clues regarding life under extreme pressure and zero-light conditions, with potential biotechnological applications in barostable enzymes and molecular cryoprotectants.

"The ocean floor is frequently compared to planetary exploration in terms of technical hostility," stated expedition director Dr. Amara Thorne. "Yet autonomy and machine-learned acoustic positioning have radically reduced expedition risk while exponentially increasing spatial resolution."`,
    source: {
      name: 'Oceanic Science Quarterly',
      url: 'https://nature.com',
    },
    author: 'Clara Moreau',
    publishedAt: '2026-09-18T14:00:00Z',
    category: 'science',
    readTimeMinutes: 6,
    imageUrl: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 4,
    likesCount: 409,
    commentsCount: 62,
  },
  {
    id: 'art-5',
    title: 'International Cultural Summit Adopts Universal Open Provenance Standard for Digital Art Archives',
    summary: 'Curators and national library directors establish cryptographic metadata guidelines to protect historical heritage documentation from synthetic degradation.',
    content: `Representatives from national museums, public archives, and digital preservation foundations concluded a week-long symposium in Vienna by signing the Vienna Charter on Heritage Provenance. The accord defines open cryptographic manifest schemas that track archival scans, optical restoration edits, and chain-of-custody verification for high-value cultural artifacts.

With generative media tools making synthetic image generation indistinguishable from historical photography, cultural institutions faced growing vulnerability to subtle archival contamination.

The new protocol introduces signed verifiable claims attached directly to file headers, allowing researchers to inspect microscopic pixel alterations, camera sensor calibration profiles, and institutional notary seals.

"Preserving human cultural history requires not only physical preservation of canvases and parchment, but mathematical guarantees for digital surrogates that future generations will study," affirmed curator Henriette Blanc.`,
    source: {
      name: 'Arts & Heritage Gazette',
      url: 'https://unesco.org',
    },
    author: 'Gabriel Mercier',
    publishedAt: '2026-09-18T12:20:00Z',
    category: 'culture',
    readTimeMinutes: 3,
    imageUrl: 'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 5,
    likesCount: 187,
    commentsCount: 21,
  },
  {
    id: 'art-6',
    title: 'Preventive Sleep Architecture Research Links Deep Wave Coherence to Cognitive Resilience',
    summary: 'Multi-cohort neuroimaging study reveals synchronized slow-wave sleep cycles act as a primary glymphatic clearance driver, mitigating neurodegenerative risk factors.',
    content: `A decade-long collaborative study tracking over 4,800 participants across eight medical research centers has quantified the direct mechanical relationship between non-REM stage 3 sleep synchrony and brain metabolic waste clearance.

Using dual-frequency magnetoencephalography alongside continuous physiological monitoring, researchers discovered that individuals with consistent slow-wave phase coupling exhibited 45% lower amyloid biomarker accretion and maintained superior spatial working memory performance into their seventh and eighth decades.

The research also highlighted the counterproductive effects of common sedative compounds, which induce unconsciousness without facilitating the rhythmic hydraulic pressure waves required for cerebrospinal fluid circulation.

Clinicians are now designing targeted circadian light interventions and non-invasive acoustic stimulation devices that pulse pink noise phase-matched to slow waves to naturally reinforce deep sleep cycles.`,
    source: {
      name: 'Medical Journal of Neurology',
      url: 'https://thelancet.com',
    },
    author: 'Dr. Evelyn Ward',
    publishedAt: '2026-09-18T10:10:00Z',
    category: 'health',
    readTimeMinutes: 5,
    imageUrl: 'https://images.unsplash.com/photo-1511295742362-92c96b124e52?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 6,
    likesCount: 673,
    commentsCount: 94,
  },
  {
    id: 'art-7',
    title: 'Diplomatic Accord Established to Protect Critical Undersea Communication Cables in International Waters',
    summary: 'Over fifty maritime nations sign binding treaty classifying submarine fiber corridors as protected infrastructure with shared surveillance patrols.',
    content: `Following multiple incidents of anchor dragging and suspicious maritime telemetry near high-density submarine communication clusters, naval representatives and telecommunications ministers convened in Geneva to establish a multilateral defense pact.

Submarine cables carry over 97% of transoceanic data traffic, facilitating trillions of dollars in daily international commerce, cloud connectivity, and intergovernmental communications. Despite their paramount economic significance, legal protections in extraterritorial waters have historically lagged behind territorial airspace and navigational shipping lanes.

The new agreement stipulates designated exclusion zones for commercial bottom trawling, mandatory real-time AIS transponder broadcast for all vessels entering sensitive coordinates, and a joint maritime rapid-response mechanism to repair cable breaks within 72 hours.`,
    source: {
      name: 'Maritime Diplomat',
      url: 'https://reuters.com',
    },
    author: 'Tariq Al-Mansoor',
    publishedAt: '2026-09-18T08:45:00Z',
    category: 'world',
    readTimeMinutes: 4,
    imageUrl: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 7,
    likesCount: 312,
    commentsCount: 45,
  },
  {
    id: 'art-8',
    title: 'Urban Architecture Embraces Passive Geothermal Cooling Envelopes in New Megacity Builds',
    summary: 'Civil engineering teams in Mediterranean and Southeast Asian metropolises integrate subterranean air exchangers to cut HVAC electrical load by 40%.',
    content: `In response to extended urban heat island phenomena, progressive architectural bureaus are looking several meters beneath building foundations for zero-emission climate control. By circulating ambient intake air through sealed subterranean concrete tubes placed deep within the thermally stable earth mantle, air is naturally pre-cooled by 8 to 12 degrees Celsius prior to reaching mechanical filtration units.

The engineering approach, modernized from ancient Persian windcatchers and Roman hypocausts, requires minimal parasitic fan power and operates without chemical refrigerants or fluorinated gases.

Initial data from three newly commissioned commercial developments in Athens and Singapore indicates a 38% reduction in peak-hour electrical demand, dramatically dampening utility brownout vulnerabilities during extreme temperature spikes.`,
    source: {
      name: 'Architectural Digest World',
      url: 'https://archdaily.com',
    },
    author: 'Lena Kowalski',
    publishedAt: '2026-09-18T07:15:00Z',
    category: 'culture',
    readTimeMinutes: 4,
    imageUrl: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80',
    isBreaking: false,
    trendingRank: 8,
    likesCount: 289,
    commentsCount: 38,
  }
];
