function ColorSelect({ label, value, options, onChange }) {
  return (
    <div className="color-select">
      <label className="color-select__label" htmlFor="target-color-select">
        {label}
      </label>

      <select
        className="color-select__control"
        id="target-color-select"
        value={value}
        onChange={onChange}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default ColorSelect;
