# Design (Problem 10)

Goal: a calm, premium Yale shop that feels alive, so shoppers stay longer, trust what they see, and buy.

## Earlier design changes (my prompts during the build)

| Change | What it looks like | Why it helps customers stay and buy |
|---|---|---|
| **Modern, minimal redesign** | Roboto everywhere (light, large headings), lots of white space, warm cream/sand backgrounds, borderless product cards | Nothing competes with the products. A clean page reads as "quality brand", which supports $58–$98 prices, and is easy to scan. |
| **Dan the Bulldog** | An original Dan illustration in the nav logo, the Home hero ("Hi, I'm Dan! Chief comfort officer."), About, the login pages, and as the chat button | A friendly mascot gives the shop personality and Yale pride, and makes the chat feel inviting, so more shoppers ask for help. |
| **Transparent product photos** | All 102 photos cut out of their black/white boxes onto the sand tiles, with smooth edges and logos kept | Mismatched black and white boxes looked cheap. Uniform cut-outs make the catalogue look like one premium collection and keep attention on the garment. |
| **Navy instead of terracotta/green** | Yale navy `#1F2E4D` for the accent (headline highlight, labels, links, nav underline, focus rings, favicon) and Dan's collar, matching the real Handsome Dan's bandana | Navy is the colour Yale fans already identify with, so the site feels official and on-brand. One accent colour also keeps the earth-tone palette calm. |

## New in Problem 10

### 1. Cards that lift on hover
- On hover (or keyboard focus), a product card rises **6 px** with a soft navy shadow under the photo. The photo zooms slightly (5%) and the name turns navy, over 0.45 s with an ease-out curve.
- **Why:** it tells the shopper "this is clickable" without buttons or clutter, and the gentle motion makes browsing feel responsive and fun, which encourages people to look at more products.

### 2. "New" and "Low stock" badges
- Small uppercase pills in the top-left corner of the card photo, in the site palette:
  - **New:** solid navy pill. The database has no "date added" field, so new arrivals are a short list the shop sets (`NEW_ARRIVALS` in `backend/tools.py`): currently the 2025 Yale vs Harvard tee, the Brooks Brothers bomber, and the Hype & Vice and Maplehouse styles.
  - **Low stock:** white pill with dark-gold text, shown when **30 or fewer units are left across all sizes**. It's computed **live** from `inventory`, so it's always true (currently 11 products). If both apply, "Low stock" wins.
- Shown on the Products page and on Dan's product cards in the chat results.
- **Why:** "New" gives returning shoppers a reason to look again. "Low stock" is honest urgency: it nudges people who are on the fence to buy before their size is gone, and it's never a fake countdown. Showing them only on some cards keeps them meaningful.

### 3. Dan tilts his head
- When the pointer is on or near Dan (the hero circle, the nav logo, the "Meet Dan" band, the chat button and header, the login pages), his head tilts **−9°** from the neck and his ears perk up. The springy, slightly overshooting motion takes 0.55 s, and his collar stays still. When the pointer leaves, he settles back.
- **Why:** a small surprise that rewards curiosity makes the site feel alive and memorable, and draws the eye to the chat button, the shop's best tool for helping shoppers find and buy the right item.

### Accessibility
All motion is turned off for visitors whose system asks for reduced motion (`prefers-reduced-motion`). Badges are real text, so screen readers announce them.
