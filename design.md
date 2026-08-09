# Design Specification: Taxon Enterprise CA Compliance Platform

## 1. Design Philosophy: "Compliance Minimalist"
The Taxon interface is designed for high-stakes financial compliance. It prioritizes **trust, clarity and precision**. The aesthetic is modern and minimalist (similar to Stripe or Vercel), utilizing generous whitespace, subtle borders and a high-contrast type scale to reduce cognitive load for Chartered Accountants managing complex data.

---

## 2. Visual Identity & Brand
- **Logo:** A professional mark combining a document icon with a rising chart trend line.
- **Brand Colors:**
  - **Primary (Accent):** `#0052ff` (Soft Blue) - Used for primary actions (buttons), progress bars and active navigation states.
  - **Success:** Soft Green (e.g., `#e6f4ea` background with `#1e8e3e` text/icon).
  - **Error:** Light Red (e.g., `#fce8e6` background with `#d93025` text/icon).
  - **Warning/Pending:** Muted Amber (e.g., `#fef7e0` background with `#f9ab00` text/icon).

---

## 3. Color Palette & Theming
Built on a light-mode foundation with high readability.

| Token | Value | Usage |
| :--- | :--- | :--- |
| **Surface (Default)** | `#fbf8ff` | Main background of the application shell. |
| **Surface Container** | `#ffffff` | Background for cards, tables and whiteboards. |
| **Surface Dim** | `#d9d9e7` | Subtle contrast for secondary backgrounds. |
| **Text Primary** | `#1a1a1a` | Headings and primary body copy. |
| **Text Secondary** | `#4a4a4a` | Labels, descriptions and metadata. |
| **Border Muted** | `#e5e7eb` | Dividers and input borders. |

---

## 4. Typography (Hanken Grotesk)
A clean, geometric sans-serif that balances modernism with corporate authority.

- **Headlines (H1/H2):** Bold weight, tight tracking, `#1a1a1a`. Used for page titles (e.g., "Statutory Audit Trail").
- **Body:** Regular weight, `14px` or `16px`. Optimized for data density in tables.
- **Labels:** Semi-bold, `12px` or `13px`, often in all-caps for navigation or secondary badges.

---

## 5. Layout Architecture (The Shell)
The application uses a persistent **Global Shell** to maintain context.

### A. Side Navigation (`SideNavBar`)
- **Width:** `280px` (Fixed).
- **Style:** Light gray background (`#f3f2ff`) with a subtle right border.
- **Components:**
  - Top: Logo and CA Firm Branding.
  - Middle: Navigation links (Dashboard, Reconciliation, Ingestion, Audit, Export, Team) with Lucide icons.
  - Bottom: Help Center and Logout.

### B. Top AppBar (`TopAppBar`)
- **Style:** Glassmorphic / White background with blur effect.
- **Components:**
  - Left: Search bar (Global search).
  - Center: **Client Workspace Dropdown** (Crucial for multi-tenant context switching).
  - Right: Notification bell, Help, Settings icon and User Profile (Avatar + Role Badge).

---

## 6. Component Patterns
### Tables (High Density)
- **Header:** Light gray background, uppercase labels, sticky position.
- **Rows:** Hover states with subtle background change; standard height for readability.
- **Status Badges:** Rounded pills with semantic background/text colors (e.g., `ACCEPT`, `REJECT`, `PENDING`).

### Data Entry & Modals
- **Inputs:** Soft gray borders (`rounded-lg`), clear focus states (`#0052ff` ring).
- **Cards:** White background, minimal shadows (elevation 0 or 1), `rounded-xl` corners.

### Interactive Elements
- **Primary Buttons:** Solid `#0052ff`, white text, `rounded-lg`, smooth hover transition.
- **Progress Bars:** Smooth animated bars showing `processed_rows / total_rows`.

---

## 7. Technical Implementation Details
- **Framework:** React + Tailwind CSS.
- **Icons:** `lucide-react`.
- **State Management:** Assume `@tanstack/react-query` for asynchronous operations (loaders/skeletons).
- **RBAC:** Visual logic should account for 4 tiers: `OWNER`, `ADMIN`, `MANAGER`, `CLERK`. Restricted actions (e.g., "Remove User") should be hidden or disabled for lower roles.
