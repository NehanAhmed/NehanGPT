# NehanGPT

A modern, full-stack AI chat application built with Flask, MongoDB, and a beautiful glassmorphism UI. NehanGPT provides a seamless chat experience with user authentication, session management, and customizable AI assistant settings.

---

## Features

- **AI Chatbot**: Interact with an advanced AI assistant.
- **User Authentication**: Register, login, and secure your account.
- **Profile Management**: Update your name and profile picture.
- **Session History**: View and manage your previous chat sessions.
- **Custom System Prompts**: Personalize the AI's behavior.
- **Password & Security**: Change your password securely.
- **Modern UI**: Responsive, glassmorphism-inspired design with dark mode.

---

## Tech Stack

- **Backend**: Flask, Flask-Login, Flask-Bcrypt, Flask-PyMongo
- **Frontend**: Bootstrap 5, FontAwesome, custom SCSS/CSS
- **Database**: MongoDB
- **AI Integration**: MistralAI (or your preferred provider)

---

## Getting Started

### 1. Clone the Repository
```sh
# Using HTTPS
git clone https://github.com/yourusername/nehan-gpt.git
cd nehan-gpt
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root:
```
MONGO_URI=your_mongodb_uri
SECRET_KEY=your_secret_key
AI_API_KEY=your_ai_api_key
```

### 4. Run the Application
```sh
python app.py
```
Visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## Project Structure

```
NehanGPT - Python Project/
├── app.py
├── mongodb.py
├── requirements.txt
├── Templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── setting.html
│   └── ...
├── Static/
│   ├── style.css
│   ├── signup.scss
│   └── Assets/
│       └── Icons/
│           └── default-avatar.jpg
└── ...
```

---

## Customization
- **AI Model**: Configure your AI provider and system prompt in the settings page.
- **UI Theme**: Modify `Static/style.css` or SCSS files for branding.

---

## License

This project is for educational and personal use. For commercial use, please check the license terms of the AI provider and dependencies.

---

## Credits
- [Bootstrap](https://getbootstrap.com/)
- [FontAwesome](https://fontawesome.com/)
- [MistralAI](https://mistral.ai/) (or your chosen AI backend)

---

## Screenshots

> Add screenshots of the chat UI, settings page, and login/register screens here.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
