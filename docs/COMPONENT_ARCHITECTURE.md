# Component Architecture

`App.jsx` owns route composition. `OfficerLayout` is the authenticated frame and provides the shared header, sidebar and contextual Ask PRAHARI drawer.

## Shared layers

- `components/layout`: immutable officer frame and navigation.
- `components/common`: KPI, section, filter and table primitives.
- `components/charts`: lightweight SVG/CSS charts and interactive India map.
- `components/project`: project header and Milestone Journey.
- `components/assistant`: contextual assistant provider, launcher and drawer.
- `pages/public`, `pages/auth`, `pages/officer`, `pages/project`: route-level composition.
- `data/mock`: presentation-ready mock contracts isolated from components.

Pages consume shared primitives rather than defining alternate headers, sidebars or assistant patterns. This keeps terminology and information hierarchy coherent across the application.
