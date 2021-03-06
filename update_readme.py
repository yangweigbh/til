import git
from datetime import timezone
import pathlib
import sys
import re

root = pathlib.Path(__file__).parent.resolve()

index_re = re.compile(r"<!\-\- index starts \-\->.*<!\-\- index ends \-\->", re.DOTALL)
count_re = re.compile(r"<!\-\- count starts \-\->.*<!\-\- count ends \-\->", re.DOTALL)

COUNT_TEMPLATE = "<!-- count starts -->{}<!-- count ends -->"

def created_changed_times(repo_path, ref="main"):
    created_changed_times = {}
    repo = git.Repo(repo_path, odbt=git.GitDB)
    commits = reversed(list(repo.iter_commits(ref)))
    for commit in commits:
        dt = commit.committed_datetime
        affected_files = list(commit.stats.files.keys())
        for filepath in affected_files:
            if filepath not in created_changed_times:
                created_changed_times[filepath] = {
                    "created": dt.isoformat(),
                    "created_utc": dt.astimezone(timezone.utc).isoformat(),
                }
    return created_changed_times


def build_database(repo_path):
    all_times = created_changed_times(repo_path)
    article_list = {}
    for item in root.iterdir():
        if item.is_file():
            continue
        if len(list(item.glob("*.md"))) == 0:
            continue
        topic = item.name
        article_list[topic] = []
        for filepath in item.iterdir():
            fp = filepath.open()
            title = fp.readline().lstrip("#").strip()
            path = str(filepath.relative_to(root))
            url = "https://github.com/yangweigbh/til/blob/main/{}".format(path)

            article_list[topic].append({"title": title, "url": url, "timestamp": all_times[path]})

        article_list[topic].sort(key=lambda article: article["timestamp"]["created_utc"], reverse=True)

    return article_list

if __name__ == "__main__":
    by_topic = build_database(root)
    index = ["<!-- index starts -->"]
    article_count = 0
    for topic, rows in by_topic.items():
        index.append("## {}\n".format(topic))
        for row in rows:
            index.append(
                "* [{title}]({url}) - {date}".format(
                    date=row["timestamp"]["created"].split("T")[0], **row
                )
            )
            article_count += 1
        index.append("")
    if index[-1] == "":
        index.pop()
    index.append("<!-- index ends -->")
    if "--rewrite" in sys.argv:
        readme = root / "README.md"
        index_txt = "\n".join(index).strip()
        readme_contents = readme.open().read()
        rewritten = index_re.sub(index_txt, readme_contents)
        rewritten = count_re.sub(COUNT_TEMPLATE.format(article_count), rewritten)
        readme.open("w").write(rewritten)
    else:
        print("\n".join(index))