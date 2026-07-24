import { useState } from 'react'

function MessageLog({ messages }) {
  const [isOpen, setIsOpen] = useState(true)

  const handleToggle = () => {
    setIsOpen((prev) => !prev)
  }

  return (
    <section className={`message-log ${!isOpen ? 'message-log--collapsed' : ''}`}>
      <div className="message-log__header">
        <h2 className="message-log__title">Журнал сообщений</h2>

        <button
          className="message-log__toggle"
          type="button"
          onClick={handleToggle}
        >
          {isOpen ? 'Свернуть' : 'Развернуть'}
        </button>
      </div>

      {isOpen && (
        <ul className="message-log__list">
          {messages.map((message) => (
            <li className="message-log__item" key={message.id}>
              {message.text}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default MessageLog