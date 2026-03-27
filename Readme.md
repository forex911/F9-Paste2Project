# ⚡ f9-Paste2Project

> Paste your folder structure → Press a key → Your entire project is created instantly 🚀

---

## 🚀 Overview

**f9** is a lightweight CLI tool that converts a pasted tree structure into real files and directories on your system.

No more manually creating folders and files.
Just paste → run → done ✅

---

## ✨ Features

* 📂 Auto-creates nested folders
* 📄 Instantly generates files
* 🌳 Supports tree-style input (`├──`, `│`, etc.)
* ⚡ Fast and lightweight
* 🧠 Smart indentation detection
* 🪟 Windows CLI support
* 💻 Zero setup after install

---

## 📦 Project Structure

```
f9/
├── f9.py
├── f9_Installer.bat
└── README.md
```

---

## ⚙️ Installation (Windows)

### 1. Clone the Repository

```bash
git clone https://github.com/forex911/f9-paste2project.git
cd f9
```

---

## 🔧 Automatic Setup (Recommended)

Run the installer:

```bash
f9_Installer.bat
```

### ✅ What it does

* Copies files to:

  ```
  C:\Users\<your-user>\AppData\Local\f9
  ```
* Creates `f9` command (`f9.bat`)
* Safely adds the folder to **User PATH (no truncation)**

---

### ⚠️ Important

After installation:

👉 **Restart your terminal (CMD / PowerShell / VS Code)**

---

## ▶️ Usage

### Step 1: Run command

```bash
f9
```

---

### Step 2: Paste structure

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

### Step 3: Finish input

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

* 🚀 Start new projects instantly
* 📁 Recreate GitHub repo structures
* 🧪 Testing folder layouts
* 👨‍💻 Competitive programming templates
* 🏗️ Backend / frontend scaffolding

---

## ⚠️ Notes

* Use proper tree format
* End folders with `/`
* Avoid invalid file names
* Restart terminal after install

---

## 🛠️ Troubleshooting

### ❌ `f9` not recognized

* Restart terminal (CMD / PowerShell / VS Code)
* Ensure PATH contains:

  ```
  C:\Users\<your-user>\AppData\Local\f9
  ```
* Run this to verify:

  ```
  echo %PATH%
  ```
* If missing, add manually via Environment Variables

---

### ⚠️ PATH truncated or broken

* Avoid using `setx PATH` (it truncates long PATH values)
* Use installer or registry method instead
* Remove broken entries like:

  ```
  C:\Users\<your-user>\AppDat
  ```

---

### ❌ Command works only with full path

* Example:

  ```
  C:\Users\<your-user>\AppData\Local\f9\f9.bat
  ```
* This means PATH is not set correctly
* Fix by adding the folder to PATH

---

### ❌ Permission issues

* Run terminal as Administrator
* Ensure you have write access to target directory

---

### ❌ Structure not creating correctly

* Ensure proper tree format:

  * Use `├──`, `│`, `└──`
  * End folders with `/`
* Avoid extra spaces or invalid characters

---

### ❌ Nothing happens after paste

* Make sure to press:

  ```
  CTRL + Z
  ENTER
  ```
* This signals end of input in Windows

---

### ✅ Still not working?

* Re-run installer
* Restart system
* Check Python is installed:

  ```
  python --version
  ```

---

### ⚠️ Windows PATH issues

This tool avoids common `setx` truncation issues by safely updating the registry.

---

## 🔮 Future Improvements

* Linux / Mac support
* JSON / YAML input
* GUI version
* VS Code extension
* Template saving

---

## 🤝 Contributing

Pull requests are welcome!

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---

## 👨‍💻 Author

**F9**

---

## 📜 License

MIT License
