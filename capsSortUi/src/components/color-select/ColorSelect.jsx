// capsSortUi/src/components/color-select/ColorSelect.jsx

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
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #a9a9a9'
        }}
      >
        {options.map((option) => (
          <option 
            key={option.value} 
            value={option.value}
            style={{
              backgroundColor: option.color || '#ffffff',
              color: ['white', 'yellow', 'pink'].includes(option.value) ? '#222' : '#fff',
              padding: '4px 8px'
            }}
          >
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default ColorSelect;