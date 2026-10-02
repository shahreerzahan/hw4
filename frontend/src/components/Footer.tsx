const YEAR = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <p>Campus Customs · Made in New Haven, with a little help from Dan.</p>
        <p>© {YEAR} Campus Customs · Vibe Coded by Shahreer</p>
      </div>
    </footer>
  )
}
