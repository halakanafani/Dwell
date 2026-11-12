# 🏢 Dwell - Holiday Home & Rental Management System (Odoo 19)

Welcome to the **Supernova Team** development repository for `dwell_management`! This module provides short-term rental management and DTCM compliance features for holiday homes in Dubai.

Follow this guide to clone the project, set up your feature branch, test your changes locally, and push your code back to GitHub.

---

## 👥 Team Assignments & GitHub Branches

Every team member must work **only** inside their assigned feature branch:

| Team Member | Feature Area | Branch Name | Key Files |
| :--- | :--- | :--- | :--- |
| **Fathimath Zehara** | Property Management & Menus | `feature/property-management` | `models/property.py`, `models/unit.py`, `views/property_views.xml`, `views/menus.xml` |
| **Afra Tazeen** | Booking & Reservations | `feature/booking-management` | `models/booking.py`, `views/booking_views.xml`, `data/cron_data.xml` |
| **Hala Kanafani** | DTCM Permits & Security | `feature/permit-management` | `models/permit.py`, `views/permit_views.xml`, `security/security.xml`, `security/ir.model.access.csv` |
| **Lilyan Yousuf** | Rental Agreements & Reports | `feature/rental-agreements` | `models/rental_agreement.py`, `views/rental_agreement_views.xml`, `data/agreement_template_data.xml`, `report/rental_agreement_report.xml` |
| **Ali Hassan** | Service & Cleaning Tasks | `feature/service-tasks` | `models/service_task.py`, `views/service_task_views.xml` |

---

## 🛠️ Step 1: Clone the Repository to Your Local Odoo Server

1. Open **VS Code** on your computer.
2. Open the built-in terminal (`Ctrl + ~` or `Terminal -> New Terminal`).
3. Navigate into your local Odoo `Workshop` addons directory:
   ```powershell
   cd "C:\Program Files\Odoo 19.0.20260714\server\workshop\Workshop"
   ```
4. Clone the repository directly into this folder:
   ```bash
   git clone https://github.com/halakanafani/dwell.git dwell_management
   ```

---

## 🌿 Step 2: Switch to Your Feature Branch

**Never work directly on the `main` branch!** Switch to your assigned feature branch before making any edits:

1. Enter your module folder:
   ```bash
   cd dwell_management
   ```
2. Create and switch to your assigned feature branch (refer to the table above):
   ```bash
   git checkout -b feature/your-assigned-branch
   ```

---

## 💻 Step 3: Add & Edit Your Assigned Files

Make your code changes inside the `dwell_management` project directory:
* **Python models:** Add your model code inside `models/`. Remember to import your Python file inside `models/__init__.py`!
* **XML views:** Add list and form views inside `views/`. *(Note for Odoo 19: Use `<list>` tags instead of `<tree>` tags!)*
* **Manifest updates:** Whenever you add a new XML view, security CSV, or data file, add its file path into the `'data'` array inside `__manifest__.py`.

---

## ⚙️ Step 4: Test Your Code in Odoo

Before pushing your changes, test your code on your local Odoo server:

1. Start your local Odoo server in VS Code.
2. Open your web browser at `http://localhost:8069`.
3. Turn on **Developer Mode** under *Settings*.
4. Navigate to **Apps** -> Click **Update Apps List** -> Click **Update**.
5. Search for **`Dwell`** in the search bar.
6. Click **Upgrade** (or **Activate**) to verify your views and menu items load without errors.

---

## 📤 Step 5: Save, Commit, and Push Your Work

Once your feature works cleanly on your local Odoo instance, commit and push your changes to GitHub:

```bash
# 1. Verify you are on your feature branch
git branch

# 2. Stage all your modified/created files
git add .

# 3. Commit your changes with a clear descriptive comment
git commit -m "feat: implemented booking reservation model and calendar view"

# 4. Push your branch to GitHub
git push -u origin feature/your-assigned-branch
```

---

## 🔀 Step 6: Create a Pull Request (PR)

1. Open [https://github.com/halakanafani/dwell](https://github.com/halakanafani/dwell) in your browser.
2. Click **"Compare & pull request"** next to your recently pushed branch.
3. Ensure the base branch is set to **`main`**.
4. Add a quick summary of your changes and request a code review from the Team Lead.
5. Click **Create Pull Request**.

---

## 🔄 Keeping Your Branch Updated

Before starting new work each day, pull the latest merged changes from `main` into your feature branch:

```bash
git checkout main
git pull origin main
git checkout feature/your-assigned-branch
git merge main
```