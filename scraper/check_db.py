"""Quick DB status check."""
import sqlite3, os

db = os.path.join(os.path.dirname(__file__), '..', 'ghostdomains.db')
c = sqlite3.connect(db)

total = c.execute('SELECT COUNT(*) FROM domains').fetchone()[0]
expired = c.execute('SELECT COUNT(*) FROM domains WHERE is_expired=1').fetchone()[0]
active = total - expired

print(f"Total domains: {total}")
print(f"Expired: {expired}")
print(f"Active (non-expired): {active}")
print()

print("Top 15 Expired Domains (by score):")
print(f"{'Domain':<35} {'Expiry':<12} {'DA':<5} {'BL':<7} {'Score':<6}")
print("-" * 70)
rows = c.execute('''
    SELECT d.domain, d.expiry_date,
           COALESCE(m.domain_authority, 0),
           COALESCE(m.backlinks, 0),
           COALESCE(m.composite_score, 0)
    FROM domains d
    LEFT JOIN domain_metrics m ON d.id = m.domain_id
    WHERE d.is_expired = 1
    ORDER BY m.composite_score DESC
    LIMIT 15
''').fetchall()
for r in rows:
    print(f"{r[0]:<35} {str(r[1] or '---'):<12} {r[2]:<5} {r[3]:<7} {r[4]:<6.1f}")

c.close()
