{
  "product": {
    "name": "TrafficIQ",
    "type": "enterprise SaaS / smart city operations center dashboard",
    "brand_attributes": [
      "mission-critical",
      "trustworthy",
      "calm under pressure",
      "precision instrumentation",
      "premium government/enterprise procurement-ready"
    ],
    "design_north_star": "Single-pane-of-glass control room UI: map-first, data-dense but calm, with progressive disclosure and strict hierarchy."
  },

  "inspiration_refs": {
    "visual_references": [
      {
        "title": "Dribbble search: smart city traffic",
        "url": "https://dribbble.com/search/smart-city-traffic",
        "takeaway": "Map-first dashboards with floating metric cards; neon accents used sparingly."
      },
      {
        "title": "Dribbble search: glassmorphism dashboard",
        "url": "https://dribbble.com/search/Glassmorphism-dashboard",
        "takeaway": "Frosted cards + subtle borders; avoid heavy gradients; rely on blur + noise."
      },
      {
        "title": "Muzli: dashboard inspirations 2026",
        "url": "https://muz.li/blog/best-dashboard-design-examples-inspirations-for-2026/",
        "takeaway": "Calm SaaS patterns: strong spacing, minimal chrome, clear states."
      },
      {
        "title": "Google Maps Heatmap Layer docs (conceptual reference)",
        "url": "https://developers.google.com/maps/documentation/javascript/heatmaplayer",
        "takeaway": "Heatmap color ramps and intensity weighting patterns (adapt to Leaflet)."
      }
    ],
    "reference_feel_keywords": [
      "Linear calm UI",
      "Vercel dashboard restraint",
      "Stripe enterprise polish",
      "control-room ergonomics"
    ]
  },

  "typography": {
    "font_pairing": {
      "ui_sans": {
        "name": "Space Grotesk",
        "fallback": "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        "usage": "All UI labels, headings, navigation, form labels"
      },
      "data_mono": {
        "name": "JetBrains Mono",
        "fallback": "IBM Plex Mono, Space Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        "usage": "Numbers, KPIs, timestamps, coordinates, route durations"
      }
    },
    "implementation_notes": {
      "google_fonts": [
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
      ],
      "css": {
        "body": "font-family: var(--font-sans);",
        "kpi": "font-family: var(--font-mono); font-variant-numeric: tabular-nums;"
      }
    },
    "type_scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "section_title": "text-sm font-semibold tracking-wide uppercase text-muted-foreground",
      "body": "text-sm md:text-base text-foreground/90",
      "small": "text-xs text-muted-foreground",
      "kpi_number": "text-2xl md:text-3xl font-semibold tracking-tight [font-variant-numeric:tabular-nums]"
    }
  },

  "color_system": {
    "mode": "dark-first with optional light toggle",
    "base_constraints": {
      "background": "#0a0a0a",
      "card": "#111111",
      "accent_primary": "#00D4FF",
      "notes": [
        "Use electric blue only for active/primary actions, focus rings, selected states, and key data highlights.",
        "Keep reading surfaces solid (no gradients). Use blur + subtle border + noise for depth.",
        "Avoid transparent backgrounds with dark text in light mode; ensure surfaces flip correctly."
      ]
    },
    "semantic_tokens": {
      "dark": {
        "--background": "#0A0A0A",
        "--foreground": "#EDEFF2",
        "--surface-0": "#0A0A0A",
        "--surface-1": "#0F1012",
        "--surface-2": "#111214",
        "--card": "#111111",
        "--card-2": "#141518",
        "--border": "rgba(255,255,255,0.08)",
        "--border-strong": "rgba(255,255,255,0.14)",
        "--muted": "#17181B",
        "--muted-foreground": "rgba(237,239,242,0.62)",
        "--primary": "#00D4FF",
        "--primary-foreground": "#001318",
        "--ring": "rgba(0,212,255,0.45)",
        "--focus": "rgba(0,212,255,0.55)",

        "--success": "#2EE59D",
        "--warning": "#F7C948",
        "--danger": "#FF4D4D",
        "--info": "#00D4FF",

        "--map-clear": "#2EE59D",
        "--map-moderate": "#F7C948",
        "--map-congested": "#FF4D4D",
        "--map-road-base": "rgba(255,255,255,0.10)",
        "--map-water": "rgba(0,212,255,0.08)",

        "--shadow-elev-1": "0 10px 30px rgba(0,0,0,0.45)",
        "--shadow-elev-2": "0 18px 60px rgba(0,0,0,0.55)",
        "--glass-bg": "rgba(17,17,17,0.62)",
        "--glass-border": "rgba(255,255,255,0.10)",
        "--glass-highlight": "rgba(0,212,255,0.10)"
      },
      "light": {
        "--background": "#F7F8FA",
        "--foreground": "#0B0D10",
        "--surface-1": "#FFFFFF",
        "--card": "#FFFFFF",
        "--border": "rgba(11,13,16,0.10)",
        "--muted": "#EEF1F5",
        "--muted-foreground": "rgba(11,13,16,0.62)",
        "--primary": "#007EA0",
        "--primary-foreground": "#FFFFFF",
        "--ring": "rgba(0,126,160,0.35)",

        "--success": "#0F9D6A",
        "--warning": "#B7791F",
        "--danger": "#D64545",
        "--info": "#007EA0"
      }
    },
    "allowed_gradients": {
      "usage": "Decorative only (hero header strip, subtle background wash behind topbar). Must be <=20% viewport.",
      "gradients": [
        {
          "name": "ops-wash",
          "css": "radial-gradient(900px circle at 20% 0%, rgba(0,212,255,0.10), transparent 55%), radial-gradient(700px circle at 80% 10%, rgba(46,229,157,0.06), transparent 60%)"
        }
      ]
    }
  },

  "design_tokens_css": {
    "where_to_apply": "/app/frontend/src/index.css (replace :root and .dark tokens to match below)",
    "css_custom_properties": ":root {\n  --font-sans: 'Space Grotesk', Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;\n  --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;\n\n  --radius: 14px;\n  --radius-sm: 10px;\n  --radius-lg: 18px;\n\n  --space-1: 4px;\n  --space-2: 8px;\n  --space-3: 12px;\n  --space-4: 16px;\n  --space-5: 20px;\n  --space-6: 24px;\n  --space-8: 32px;\n  --space-10: 40px;\n\n  --glass-blur: 14px;\n  --glass-sat: 140%;\n}\n\n.dark {\n  --background: 0 0% 4%; /* fallback for shadcn */\n  --foreground: 210 20% 96%;\n\n  /* TrafficIQ custom */\n  --tiq-bg: #0A0A0A;\n  --tiq-card: #111111;\n  --tiq-card-2: #141518;\n  --tiq-border: rgba(255,255,255,0.08);\n  --tiq-border-strong: rgba(255,255,255,0.14);\n  --tiq-muted: rgba(237,239,242,0.62);\n  --tiq-primary: #00D4FF;\n  --tiq-success: #2EE59D;\n  --tiq-warning: #F7C948;\n  --tiq-danger: #FF4D4D;\n\n  --tiq-glass-bg: rgba(17,17,17,0.62);\n  --tiq-glass-border: rgba(255,255,255,0.10);\n  --tiq-glass-highlight: rgba(0,212,255,0.10);\n\n  --tiq-shadow-1: 0 10px 30px rgba(0,0,0,0.45);\n  --tiq-shadow-2: 0 18px 60px rgba(0,0,0,0.55);\n}\n",
    "tailwind_usage_notes": [
      "Prefer Tailwind classes for layout; use CSS vars for colors to keep theme toggle simple.",
      "Use `bg-[var(--tiq-card)]` and `border-[var(--tiq-border)]` patterns for custom surfaces.",
      "For focus rings: `focus-visible:ring-2 focus-visible:ring-[var(--tiq-primary)]/40` (no transition:all)."
    ]
  },

  "layout": {
    "global_shell": {
      "pattern": "Sidebar + Topbar + Content",
      "sidebar_width": "w-[280px] (desktop), collapsible drawer on mobile",
      "topbar_height": "h-14 md:h-16",
      "content_max_width": "max-w-[1600px] (centered within content area only, not whole app)",
      "grid": {
        "desktop": "12-col grid with 24px gaps",
        "mobile": "single column; map becomes first; stats become horizontal scroll"
      },
      "page_padding": "px-4 sm:px-6 lg:px-8 py-6",
      "zoning": {
        "primary_zone": "Map + KPI cards + gauge (center/left)",
        "secondary_zone": "Alerts drawer/right rail + filters",
        "progressive_disclosure": "Details open in Sheet/Drawer instead of new pages when possible"
      }
    },
    "dashboard_layout": {
      "top_row": "4 KPI cards (2x2 on md, 4x1 on lg)",
      "main_row": "Map (8 cols) + Gauge + mini list (4 cols)",
      "bottom_row": "Recent incidents table + small trend chart"
    },
    "prediction_panel_layout": {
      "left": "Forecast form (Card) with toggles",
      "right": "Animated line chart + confidence band",
      "mobile": "form first, chart second"
    },
    "route_optimization_layout": {
      "top": "Start/End inputs + constraints",
      "middle": "3 route comparison table",
      "right": "Map highlight layer",
      "mobile": "table becomes cards with expandable details"
    },
    "analytics_layout": {
      "row1": "Hour-of-day bar chart + Top roads list",
      "row2": "7x24 heatmap full width",
      "row3": "Scatter plot (weather vs congestion) + holiday impact card"
    },
    "alerts_layout": {
      "pattern": "Right-side feed with filters; detail opens in Sheet",
      "mobile": "Alerts as full-screen Drawer"
    }
  },

  "components": {
    "shadcn_primary_components": {
      "navigation": [
        { "name": "Sheet", "path": "/app/frontend/src/components/ui/sheet.jsx", "use": "Mobile sidebar + alert detail panel" },
        { "name": "NavigationMenu", "path": "/app/frontend/src/components/ui/navigation-menu.jsx", "use": "Optional topbar quick actions" },
        { "name": "Breadcrumb", "path": "/app/frontend/src/components/ui/breadcrumb.jsx", "use": "Analytics drill-down" }
      ],
      "surfaces": [
        { "name": "Card", "path": "/app/frontend/src/components/ui/card.jsx", "use": "All panels; apply glass recipe" },
        { "name": "Separator", "path": "/app/frontend/src/components/ui/separator.jsx", "use": "Section dividers" },
        { "name": "ScrollArea", "path": "/app/frontend/src/components/ui/scroll-area.jsx", "use": "Alerts feed + tables" }
      ],
      "inputs": [
        { "name": "Select", "path": "/app/frontend/src/components/ui/select.jsx", "use": "City selector, time range" },
        { "name": "Calendar", "path": "/app/frontend/src/components/ui/calendar.jsx", "use": "Date range selection" },
        { "name": "Switch", "path": "/app/frontend/src/components/ui/switch.jsx", "use": "Dark/light toggle, factor toggles" },
        { "name": "Slider", "path": "/app/frontend/src/components/ui/slider.jsx", "use": "Weighting constraints for route optimization" },
        { "name": "Input", "path": "/app/frontend/src/components/ui/input.jsx", "use": "Start/end, search roads" },
        { "name": "Textarea", "path": "/app/frontend/src/components/ui/textarea.jsx", "use": "Operator notes" }
      ],
      "data_display": [
        { "name": "Badge", "path": "/app/frontend/src/components/ui/badge.jsx", "use": "Severity badges" },
        { "name": "Table", "path": "/app/frontend/src/components/ui/table.jsx", "use": "Route comparison + top roads" },
        { "name": "Tabs", "path": "/app/frontend/src/components/ui/tabs.jsx", "use": "Analytics subviews" },
        { "name": "Tooltip", "path": "/app/frontend/src/components/ui/tooltip.jsx", "use": "Map segment hover details" },
        { "name": "Progress", "path": "/app/frontend/src/components/ui/progress.jsx", "use": "Inline congestion bars" },
        { "name": "Skeleton", "path": "/app/frontend/src/components/ui/skeleton.jsx", "use": "Loading states" }
      ],
      "feedback": [
        { "name": "Sonner", "path": "/app/frontend/src/components/ui/sonner.jsx", "use": "Toasts for WS updates, export success" },
        { "name": "Alert", "path": "/app/frontend/src/components/ui/alert.jsx", "use": "Inline warnings" },
        { "name": "Dialog", "path": "/app/frontend/src/components/ui/dialog.jsx", "use": "Export PDF confirmation" }
      ]
    },

    "custom_components_to_build": [
      {
        "name": "AppShell",
        "purpose": "Sidebar + Topbar + content layout with responsive behavior",
        "notes": "Use Sheet for mobile sidebar; keep sidebar fixed on desktop."
      },
      {
        "name": "KpiStatCard",
        "purpose": "Glass card with label + big number + delta chip + sparkline",
        "micro_interactions": "Hover lifts (translateY -2) + border brightens; number count-up on mount/update"
      },
      {
        "name": "ArcGauge",
        "purpose": "Animated arc gauge for congestion index",
        "implementation_hint": "SVG arc with stroke-dasharray animation; color changes by thresholds"
      },
      {
        "name": "LeafletTrafficMap",
        "purpose": "Leaflet map with road segments colored by congestion + pulsing updates",
        "implementation_hint": "Use GeoJSON layer; animate via CSS class toggles on update"
      },
      {
        "name": "AlertsRightRail",
        "purpose": "Right-side feed with filters + slide-in animation",
        "implementation_hint": "Use ScrollArea; each item is a button opening Sheet with details"
      },
      {
        "name": "HeatmapGrid7x24",
        "purpose": "7 days x 24 hours heatmap",
        "implementation_hint": "Use CSS grid 24 columns; tooltips on cells; legend below"
      }
    ]
  },

  "glassmorphism_recipe": {
    "card_class": "bg-[var(--tiq-glass-bg)] backdrop-blur-[var(--glass-blur)] backdrop-saturate-[var(--glass-sat)] border border-[var(--tiq-glass-border)] shadow-[var(--tiq-shadow-1)] rounded-[var(--radius)]",
    "hover_class": "hover:border-[var(--tiq-border-strong)] hover:shadow-[var(--tiq-shadow-2)]",
    "inner_highlight": "before:content-[''] before:absolute before:inset-0 before:rounded-[var(--radius)] before:bg-[radial-gradient(600px_circle_at_20%_0%,rgba(0,212,255,0.10),transparent_55%)] before:pointer-events-none",
    "notes": [
      "Do not reduce opacity so much that text loses contrast.",
      "Use blur on the card container only; keep text fully opaque.",
      "Avoid gradients on content surfaces; use the inner highlight pseudo-element instead."
    ]
  },

  "data_viz": {
    "libraries": {
      "recharts": {
        "use_cases": ["line chart prediction", "bar chart hour-of-day", "scatter weather impact"],
        "styling": {
          "grid": "stroke: rgba(255,255,255,0.08)",
          "axis": "tick: rgba(237,239,242,0.62)",
          "line_primary": "stroke: var(--tiq-primary); strokeWidth: 2.5; dot: false",
          "area_confidence": "fill: rgba(0,212,255,0.12)",
          "tooltip": "Use shadcn Card-like tooltip with mono numbers"
        }
      },
      "framer_motion": {
        "use_cases": ["page transitions", "stat card entrance", "alerts slide-in", "drawer animations"],
        "motion_tokens": {
          "ease": "[0.22, 1, 0.36, 1]",
          "fast": "0.18s",
          "base": "0.28s",
          "slow": "0.45s"
        },
        "patterns": [
          "Use stagger for KPI cards (delay 0.04s each)",
          "Use layoutId for route highlight transitions",
          "Respect prefers-reduced-motion"
        ]
      },
      "leaflet": {
        "use_cases": ["live map", "route highlight", "segment tooltips"],
        "map_style": {
          "base": "Prefer dark tiles; reduce label clutter; keep roads visible",
          "segment_colors": {
            "clear": "var(--map-clear)",
            "moderate": "var(--map-moderate)",
            "congested": "var(--map-congested)"
          },
          "pulse_animation": "On WS update, add class `tiq-pulse` to updated segments for 900ms"
        }
      }
    },

    "chart_layout_rules": [
      "Always include a legend or inline labels for color meaning.",
      "Use monospace for axis values and tooltips.",
      "Avoid overly saturated fills; prefer strokes + subtle area fills."
    ],

    "heatmap_7x24": {
      "color_ramp": [
        { "stop": 0.0, "color": "rgba(46,229,157,0.18)" },
        { "stop": 0.5, "color": "rgba(247,201,72,0.22)" },
        { "stop": 1.0, "color": "rgba(255,77,77,0.26)" }
      ],
      "cell_style": "rounded-[10px] border border-[var(--tiq-border)]",
      "hover": "hover:border-[var(--tiq-border-strong)] hover:brightness-110",
      "tooltip": "Tooltip shows day, hour, avg speed, congestion index"
    }
  },

  "map_segment_rules": {
    "segment_width": "3px (default), 5px (selected route)",
    "segment_opacity": "0.9",
    "selected_route": {
      "stroke": "var(--tiq-primary)",
      "glow": "drop-shadow(0 0 10px rgba(0,212,255,0.35))"
    },
    "update_pulse_css": ".tiq-pulse { animation: tiqPulse 0.9s ease-out 1; }\n@keyframes tiqPulse {\n  0% { filter: drop-shadow(0 0 0 rgba(0,212,255,0)); opacity: 0.85; }\n  40% { filter: drop-shadow(0 0 12px rgba(0,212,255,0.35)); opacity: 1; }\n  100% { filter: drop-shadow(0 0 0 rgba(0,212,255,0)); opacity: 0.9; }\n}"
  },

  "alerts": {
    "severity_styles": {
      "critical": {
        "badge": "bg-[rgba(255,77,77,0.14)] text-[#FFB3B3] border border-[rgba(255,77,77,0.28)]",
        "dot": "bg-[#FF4D4D]",
        "ring": "ring-1 ring-[rgba(255,77,77,0.35)]"
      },
      "high": {
        "badge": "bg-[rgba(247,201,72,0.14)] text-[#FFE3A3] border border-[rgba(247,201,72,0.28)]",
        "dot": "bg-[#F7C948]",
        "ring": "ring-1 ring-[rgba(247,201,72,0.35)]"
      },
      "medium": {
        "badge": "bg-[rgba(0,212,255,0.12)] text-[#BDEFFF] border border-[rgba(0,212,255,0.22)]",
        "dot": "bg-[#00D4FF]",
        "ring": "ring-1 ring-[rgba(0,212,255,0.30)]"
      },
      "low": {
        "badge": "bg-[rgba(46,229,157,0.12)] text-[#B9F7DE] border border-[rgba(46,229,157,0.22)]",
        "dot": "bg-[#2EE59D]",
        "ring": "ring-1 ring-[rgba(46,229,157,0.30)]"
      }
    },
    "feed_item": {
      "layout": "Left: severity dot + title; Right: timestamp + chevron",
      "interaction": "Entire row is a button; hover highlights; click opens Sheet with details",
      "animation": "New alerts slide in from right (Framer Motion)"
    },
    "filters": ["severity", "city", "type", "time range"],
    "simulate_incident_button": {
      "style": "Primary button with electric blue outline + subtle glow",
      "placement": "Top of Alerts page and also in Dashboard right rail"
    }
  },

  "buttons_and_controls": {
    "button_style": "Professional / Corporate with premium glow",
    "primary_button": {
      "class": "bg-[var(--tiq-primary)] text-[var(--tiq-primary-foreground)] hover:brightness-110 active:brightness-95 focus-visible:ring-2 focus-visible:ring-[var(--tiq-primary)]/40",
      "radius": "rounded-[12px]",
      "motion": "transition-colors duration-200"
    },
    "secondary_button": {
      "class": "bg-transparent border border-[var(--tiq-border-strong)] text-foreground hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-[var(--tiq-primary)]/35",
      "motion": "transition-colors duration-200"
    },
    "ghost_button": {
      "class": "bg-transparent text-foreground/80 hover:text-foreground hover:bg-white/5",
      "motion": "transition-colors duration-200"
    },
    "toggle_switch": {
      "notes": "Use shadcn Switch; ensure thumb contrast in both themes; add data-testid"
    }
  },

  "micro_interactions": {
    "hover": [
      "Cards: translate-y-[-2px] + border brightens (no transition:all)",
      "Table rows: subtle background wash `hover:bg-white/3`",
      "Map segments: tooltip appears with 120ms delay"
    ],
    "press": ["Buttons: active:scale-[0.98] (apply only to button, not container)"],
    "loading": [
      "Use Skeleton blocks matching final layout",
      "Map: show blurred placeholder with shimmer overlay"
    ],
    "ws_updates": [
      "Pulse updated road segments",
      "Toast: 'Live update received' (sonner) only when significant changes occur"
    ],
    "page_transitions": "Fade + slight y (8px) on route change; keep under 280ms"
  },

  "accessibility": {
    "contrast": [
      "All text on glass cards must meet WCAG AA; if not, increase opacity of glass bg or use solid card bg.",
      "Never rely on color alone for severity: include label text + icon/dot."
    ],
    "focus": [
      "Use focus-visible rings with electric blue; ensure ring is visible on both dark and light.",
      "Keyboard navigation: sidebar items, table rows (as buttons), alert items must be reachable."
    ],
    "reduced_motion": "Respect prefers-reduced-motion: disable count-up and reduce map pulse intensity"
  },

  "responsive_rules": {
    "breakpoints": {
      "sm": "640px",
      "md": "768px",
      "lg": "1024px",
      "xl": "1280px",
      "2xl": "1536px"
    },
    "mobile_first_patterns": [
      "Sidebar becomes Sheet (hamburger)",
      "KPI cards become horizontal scroll with snap",
      "Right rail becomes bottom Drawer",
      "Tables become stacked cards with expandable details"
    ]
  },

  "testing_attributes": {
    "rule": "All interactive and key informational elements MUST include data-testid (kebab-case).",
    "examples": [
      "data-testid=\"topbar-city-selector\"",
      "data-testid=\"theme-toggle-switch\"",
      "data-testid=\"dashboard-congestion-index-kpi\"",
      "data-testid=\"alerts-feed-item\"",
      "data-testid=\"route-compare-select-route-1\"",
      "data-testid=\"export-pdf-button\"",
      "data-testid=\"simulate-incident-button\""
    ]
  },

  "image_urls": {
    "note": "Image selector tool unavailable in this environment. Use CSS noise + vector map styling instead of heavy photography.",
    "recommended_assets": [
      {
        "category": "background_texture",
        "description": "Subtle noise overlay (CSS) to avoid flat dark surfaces",
        "url": "(generate via CSS; no external URL)"
      },
      {
        "category": "empty_state_illustrations",
        "description": "Use lightweight inline SVG icons (lucide-react) instead of photos",
        "url": "(no external URL)"
      }
    ]
  },

  "instructions_to_main_agent": {
    "critical_fixes": [
      "Remove centered layout from App.css: do NOT use `.App-header { align-items:center; justify-content:center; }` for the app shell.",
      "Update /app/frontend/src/index.css tokens to match TrafficIQ dark-first palette; keep shadcn variables consistent.",
      "Use JS (.jsx/.js) components only (no .tsx)."
    ],
    "implementation_priorities": [
      "Build AppShell with Sidebar + Topbar; wire city selector + theme toggle.",
      "Implement Leaflet map with GeoJSON segments and pulse animation on WS updates.",
      "Implement KPI cards with count-up and monospace numbers.",
      "Implement Alerts right rail with Sheet details and severity badges.",
      "Implement Analytics heatmap grid 7x24 with tooltip + legend."
    ],
    "performance_notes": [
      "Throttle WS-driven UI updates (batch state updates every 250–500ms).",
      "Avoid re-rendering the entire map on each update; update only changed layers.",
      "Prefer CSS animations for pulse; keep Framer Motion for layout/entrance only."
    ]
  },

  "appendix_general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
