// Dan the Bulldog: an original flat illustration of our mascot, drawn in the site's earth tones.
export default function DanTheBulldog({ className, title = 'Dan the Bulldog' }: { className?: string; title?: string }) {
  return (
    <svg className={className} viewBox="0 0 260 260" role="img" aria-label={title} xmlns="http://www.w3.org/2000/svg">
      <title>{title}</title>

      {/* Collar and tag (behind the jowls) */}
      <path d="M58 196 C96 214 164 214 202 196 L206 212 C166 232 94 232 54 212 Z" fill="#5E6B4E" />
      <circle cx="130" cy="236" r="14" fill="#C9A227" />
      <circle cx="130" cy="236" r="10.5" fill="none" stroke="#A88620" strokeWidth="1.5" />
      <text x="130" y="241.5" textAnchor="middle" fontFamily="Roboto, sans-serif" fontWeight="700" fontSize="15" fill="#3A2A22">
        Y
      </text>

      {/* Small folded rose ears */}
      <path d="M44 74 C30 56 36 36 58 38 C72 40 80 50 80 62 Z" fill="#8C5A3C" />
      <path d="M216 74 C230 56 224 36 202 38 C188 40 180 50 180 62 Z" fill="#8C5A3C" />

      {/* Wide, flat head */}
      <path
        d="M130 42 C192 42 236 68 238 116 C240 150 226 176 200 190 C178 202 156 206 130 206 C104 206 82 202 60 190 C34 176 20 150 22 116 C24 68 68 42 130 42 Z"
        fill="#D4A77E"
      />

      {/* White blaze running into the muzzle */}
      <path d="M130 46 C120 46 114 62 116 84 C117 96 122 104 130 106 C138 104 143 96 144 84 C146 62 140 46 130 46 Z" fill="#F6EEE3" />

      {/* Forehead wrinkles */}
      <path d="M70 76 C86 66 102 66 112 72" stroke="#A9764F" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      <path d="M190 76 C174 66 158 66 148 72" stroke="#A9764F" strokeWidth="3.5" fill="none" strokeLinecap="round" />
      <path d="M86 62 C96 57 106 57 112 60" stroke="#B98A63" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      <path d="M174 62 C164 57 154 57 148 60" stroke="#B98A63" strokeWidth="2.5" fill="none" strokeLinecap="round" />

      {/* Wide-set eyes with heavy lids */}
      <ellipse cx="80" cy="102" rx="12" ry="12" fill="#2E211B" />
      <ellipse cx="180" cy="102" rx="12" ry="12" fill="#2E211B" />
      <circle cx="84" cy="102" r="3.4" fill="#FFFFFF" />
      <circle cx="184" cy="102" r="3.4" fill="#FFFFFF" />
      <path d="M66 98 C70 86 90 86 94 98 Z" fill="#C2946C" />
      <path d="M166 98 C170 86 190 86 194 98 Z" fill="#C2946C" />

      {/* Droopy jowls hanging below the chin */}
      <path
        d="M130 112 C104 110 66 118 52 146 C40 172 56 202 88 204 C108 205 122 196 130 186 C138 196 152 205 172 204 C204 202 220 172 208 146 C194 118 156 110 130 112 Z"
        fill="#F6EEE3"
      />

      {/* Nose rope wrinkle */}
      <path d="M90 120 C108 102 152 102 170 120" stroke="#C9A07B" strokeWidth="5" fill="none" strokeLinecap="round" />

      {/* Broad, pushed-up nose */}
      <path d="M104 122 C104 110 156 110 156 122 C156 134 142 140 130 140 C118 140 104 134 104 122 Z" fill="#3A2A22" />
      <ellipse cx="116" cy="120" rx="5" ry="2.6" fill="#5C4638" />
      <ellipse cx="119" cy="128" rx="3" ry="2" fill="#241812" />
      <ellipse cx="141" cy="128" rx="3" ry="2" fill="#241812" />
      <path d="M130 140 L130 152" stroke="#3A2A22" strokeWidth="3" strokeLinecap="round" />

      {/* Upper lip line drooping over the jaw */}
      <path d="M84 158 C104 172 120 166 130 152 C140 166 156 172 176 158" stroke="#3A2A22" strokeWidth="3" fill="none" strokeLinecap="round" />

      {/* Underbite: lower jaw juts forward with teeth pointing up */}
      <path d="M100 172 C108 160 152 160 160 172 C158 190 102 190 100 172 Z" fill="#7A3E2A" />
      <path d="M106 175 C112 186 148 186 154 175 C146 181 114 181 106 175 Z" fill="#B5603C" />
      <path d="M104 172 L108 158 L114 170 Z" fill="#FFFFFF" />
      <path d="M156 172 L152 158 L146 170 Z" fill="#FFFFFF" />

      {/* Whisker dots */}
      <circle cx="84" cy="140" r="2" fill="#D9C9B5" />
      <circle cx="92" cy="147" r="2" fill="#D9C9B5" />
      <circle cx="80" cy="150" r="2" fill="#D9C9B5" />
      <circle cx="176" cy="140" r="2" fill="#D9C9B5" />
      <circle cx="168" cy="147" r="2" fill="#D9C9B5" />
      <circle cx="180" cy="150" r="2" fill="#D9C9B5" />
    </svg>
  )
}
