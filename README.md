# 🐙 GitHub Activity Viewer

<p align="center">
  <img src="https://via.placeholder.com/150x150.png?text=Logo" alt="Project Logo" width="150">
</p>

<h3 align="center">A sleek, professional desktop application for monitoring GitHub user activity in real-time.</h3>

<p align="center">
  <img alt="Python Version" src="https://img.shields.io/badge/python-3.8+-blue.svg">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green.svg">
  <img alt="Status" src="https://img.shields.io/badge/status-active-brightgreen.svg">
  <img alt="PyQt6" src="https://img.shields.io/badge/UI-PyQt6-orange.svg">
</p>

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-screenshots">Screenshots</a> •
  <a href="#-technology-stack">Tech Stack</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</p>

---

![GIF of the app in action](https://via.placeholder.com/800x450.gif?text=App+Demonstration+GIF)

## ✨ Key Features

-   **Seamless Performance**: A fully multi-threaded architecture ensures the UI remains fluid and responsive, even while fetching data.
-   **Intelligent Caching**: Smart caching mechanism reduces API calls, provides faster load times for recent searches, and respects GitHub's rate limits.
-   **API Rate Limit Display**: Always stay informed about your current GitHub API consumption with a real-time display.
-   **Dual-Theme Interface**: Switch effortlessly between a crisp light theme and a slick dark theme to suit your preference.
-   **Rich User Profiles**: View user avatars and essential profile information at a glance.
-   **Event-Specific Icons**: A unique icon for each event type (Push, Issue, PR, etc.) makes the activity feed easy to scan and understand.
-   **Direct GitHub Links**: Double-click any event in the table to instantly open its corresponding URL on GitHub in your default browser.

## 🚀 Installation

Get up and running in a few simple steps.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Tropixy/Github-Activity.git
    cd Github-Activity
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # Create the environment
    python -m venv venv

    # Activate it
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🎮 Usage

Once the installation is complete, you can launch the application by running:

```bash
python "Github Activity.py"
```

1.  Enter a valid GitHub username in the input field.
2.  Press `Enter` or click the "Show Activity" button.
3.  The user's recent public activity will be fetched and displayed in the table.

## 📸 Screenshots

<p align="center">
  <strong>Dark Theme</strong><br>
  <img src="https://via.placeholder.com/800x600.png?text=Dark+Theme+Screenshot" alt="Dark Theme Screenshot" width="70%">
</p>
<p align="center">
  <strong>Light Theme</strong><br>
  <img src="https://via.placeholder.com/800x600.png?text=Light+Theme+Screenshot" alt="Light Theme Screenshot" width="70%">
</p>

## 🛠️ Technology Stack

This project is built with a modern set of tools:

-   **[Python 3](https://www.python.org/)**: Core programming language.
-   **[PyQt6](https://pypi.org/project/PyQt6/)**: For building the rich graphical user interface.
-   **[qtawesome](https://pypi.org/project/qtawesome/)**: For easily embedding stunning FontAwesome icons.
-   **[requests](https://pypi.org/project/requests/)**: For elegant and simple HTTP requests to the GitHub API.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License.
