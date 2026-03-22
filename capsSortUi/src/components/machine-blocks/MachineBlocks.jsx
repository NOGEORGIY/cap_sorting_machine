function MachineBlocks({ blocks }) {
  return (
    <section className="machine-blocks">
      <h2 className="machine-blocks__title">Блоки машины</h2>

      <ul className="machine-blocks__list">
        {blocks.map((block) => (
          <li className="machine-blocks__item" key={block.id}>
            <span className="machine-blocks__name">{block.name}</span>
            <span className="machine-blocks__status">{block.status}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default MachineBlocks