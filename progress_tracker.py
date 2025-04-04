import re
from datetime import datetime, timedelta

class ProgressTracker:
    def __init__(self, filename):
        self.filename = filename
        self.categories = []
        self.total_hours = 0
        self.parse_roadmap()
        
    def parse_roadmap(self):
        current_category = None
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Detect category headers
                    category_match = re.match(r'^## (.+) - Total: (\d+)h', line)
                    if category_match:
                        current_category = {
                            'name': category_match.group(1),
                            'total_time': int(category_match.group(2)),
                            'tasks': [],
                            'done_time': 0,
                            'remaining_time': 0,
                            'done_tasks': 0
                        }
                        self.categories.append(current_category)
                        self.total_hours += current_category['total_time']
                        continue
                    
                    # Parse task lines - more robust pattern
                    task_match = re.match(
                        r'^\|(.+?)\|.*?(\d+)h\s*\|.*?(Low|Medium|High)\s*\|.*?([✅\[x\]])\s*\|', 
                        line
                    )
                    if current_category and task_match:
                        task_name = task_match.group(1).strip()
                        task_time = int(task_match.group(2))
                        task_difficulty = task_match.group(3)
                        task_status = task_match.group(4)
                        
                        task = {
                            'name': task_name,
                            'time': task_time,
                            'difficulty': task_difficulty,
                            'done': '✅' in task_status or 'x' in task_status.lower()
                        }
                        current_category['tasks'].append(task)
                        if task['done']:
                            current_category['done_time'] += task['time']
                            current_category['done_tasks'] += 1
                        else:
                            current_category['remaining_time'] += task['time']
        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found.")
            exit(1)
    
    def print_progress(self):
        if not self.categories:
            print("No categories found in the roadmap file.")
            return
            
        total_tasks = sum(len(c['tasks']) for c in self.categories)
        if total_tasks == 0:
            print("No tasks found in any categories.")
            print("Please check your markdown file format.")
            print("Expected format for tasks:")
            print("| Task name | 2h | Medium | [ ] |")
            return
            
        total_done = sum(c['done_time'] for c in self.categories)
        done_tasks = sum(c['done_tasks'] for c in self.categories)
        
        # Calculate estimated completion
        remaining_hours = max(0, self.total_hours - total_done)
        avg_hours_per_day = 3
        completion_date = datetime.now() + timedelta(days=remaining_hours/avg_hours_per_day)
        
        print(f"\n📊 Overall Progress: {done_tasks}/{total_tasks} tasks ({done_tasks/total_tasks:.0%})")
        print(f"⏱️ Time: {total_done}h/{self.total_hours}h ({total_done/self.total_hours:.0%}) - {remaining_hours}h remaining")
        print(f"📅 Estimated completion: {completion_date.strftime('%b %d')} at {avg_hours_per_day}h per day")
        print("="*50)
        
        for cat in self.categories:
            if not cat['tasks']:
                continue
                
            completion = cat['done_tasks']/len(cat['tasks'])
            print(f"\n{cat['name']}:")
            print(f"  {cat['done_tasks']}/{len(cat['tasks'])} tasks ({completion:.0%})")
            print(f"  Time: {cat['done_time']}h/{cat['total_time']}h")
            
            # Print remaining high-priority tasks
            high_priority = [t for t in cat['tasks'] if not t['done'] and t['difficulty'] == 'High']
            if high_priority:
                print("  🔴 Remaining critical:")
                for task in high_priority:
                    print(f"    - {task['name']} ({task['time']}h)")

if __name__ == "__main__":
    tracker = ProgressTracker('INTEGRATED_ROADMAP.md')
    tracker.print_progress()