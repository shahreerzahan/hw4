const YEAR = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="footer">
      <p>
        <strong>Campus Customs</strong> · Made in New Haven with Bulldog spirit 💙
      </p>
      <p className="footer-small">© {YEAR} Campus Customs. A class project for MGT 409.</p>
    </footer>
  )
}
