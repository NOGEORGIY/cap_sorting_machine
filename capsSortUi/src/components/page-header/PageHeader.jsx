function PageHeader({ title }) {
  return (
    <header className="page-header">
      <div className="page-header__inner">
        <div className="page-header__logo" aria-hidden="true">
          ⚙
        </div>

        <h1 className="page-header__title">{title}</h1>
      </div>
    </header>
  )
}

export default PageHeader