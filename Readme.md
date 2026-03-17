# ⚡ F9-Paste2Project

> Paste your folder structure → Press a key → Your entire project is created instantly 🚀

---

## 🚀 Overview

**F9-Paste2Project** is a powerful CLI tool that converts a pasted tree structure into real files and directories on your system.

No more manually creating folders and files.
Just paste → run → done ✅

---

## ✨ Features

* 📂 Auto-creates nested folders
* 📄 Instantly generates files
* 🌳 Supports tree-style input (`├──`, `│`, etc.)
* ⚡ Fast and lightweight
* 🧠 Smart indentation detection
* 🪟 Windows support with installer
* 💻 Simple CLI usage

---

## 📦 Project Structure

```
F9-Paste2Project/
├── f9.py
├── f9_Installer.bat
└── README.md
```

---

## ⚙️ Installation (Windows)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/F9-Paste2Project.git
cd F9-Paste2Project
```

---

### 2. Run Installer

```bash
f9_Installer.bat
```

This will:

* Add `f9` as a global command
* Allow you to run it from anywhere

---

## ▶️ Usage

### Step 1: Run Command

```bash
f9
```

---

### Step 2: Paste Your Structure

Example:

```
my-app/
├── src/
│   ├── index.js
│   └── app.js
├── public/
│   └── index.html
└── package.json
```

---

### Step 3: Finish Input

Press:

```
CTRL + Z
ENTER
```

---

## ✅ Output

```
DIR:  my-app
DIR:  my-app/src
FILE: my-app/src/index.js
FILE: my-app/src/app.js
DIR:  my-app/public
FILE: my-app/public/index.html
FILE: my-app/package.json
```

🎉 Your project structure is created instantly!

---

## 🧠 How It Works

* Reads pasted input line-by-line
* Detects indentation level
* Uses a stack to track directory hierarchy
* Creates:

  * folders → `Path.mkdir()`
  * files → `Path.touch()`

---

## 📌 Example Use Cases

* 🚀 Start new projects quickly
* 📁 Recreate GitHub repo structures
* 🧪 Testing folder layouts
* 👨‍💻 Competitive programming templates
* 🏗️ Backend / frontend scaffolding

---

## ⚠️ Important Notes

* Use proper tree format
* End folders with `/`
* Avoid invalid file names
* Works best with consistent indentation

---

## 🔮 Future Improvements

* Linux / Mac support
* JSON / YAML input support
* GUI version
* VS Code extension
* Template saving feature

---

## 🤝 Contributing

Pull requests are welcome!

Feel free to:

* Improve parsing logic
* Add new features
* Optimize performance

---

## ⭐ Support

If you found this useful, give it a ⭐ on GitHub!

---

## 👨‍💻 Author

**F9**

---

## 📜 License

MIT License
