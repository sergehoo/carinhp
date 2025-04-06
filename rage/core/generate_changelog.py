from core.version import bump_version, get_version
from datetime import datetime
import sys

CHANGELOG_PATH = "CHANGELOG.md"

def main(level="patch"):
    new_version = bump_version(level)
    today = datetime.today().strftime("%Y-%m-%d")

    changelog_entry = f"""\
## [{new_version}] - {today}
### Ajouté
- (À remplir)

### Modifié
- (À remplir)

### Corrigé
- (À remplir)

---

"""
    with open(CHANGELOG_PATH, "r+") as f:
        content = f.read()
        f.seek(0, 0)
        f.write(changelog_entry + content)

    print(f"✅ Version bumpée en {new_version} et changelog mis à jour.")

if __name__ == "__main__":
    niveau = sys.argv[1] if len(sys.argv) > 1 else "patch"
    main(niveau)