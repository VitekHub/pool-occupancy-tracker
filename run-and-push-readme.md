## Schedule Task with Windows Task Scheduler

### Open Task Scheduler

- Press `Win + S`, type **Task Scheduler**, and open it.

---

### Create Task

Click **Create Task** (not Basic Task).

#### General Tab

- **Name**: `pool-occupancy-tracker-automatic`
- ✅ **Run whether user is logged on or not**
  - ✅ **Do not store password**
- ✅ **Run with highest privileges**
- ✅ **Hidden**

#### Triggers Tab → New

- **Begin the task**: `Daily`
- **Start**: `6:00 AM`
- ✅ **Repeat task every**: `10 minutes`
- **For a duration of**: `16 hours` (ends at 10 PM)
- ✅ **Enabled**

#### Actions Tab → New

- **Action**: `Start a program`
- **Program/script**: `cmd.exe`
- **Add arguments**: `/c "C:\path\to\your\repo\run_and_push.bat"`
- **Start in**: `C:\path\to\your\repo`

#### Conditions Tab

- ❌ Uncheck *Start the task only if the computer is on AC power* (if you want it to run on battery)
- ✅ **Start only if the following network connection is available:** (Any connection)

#### Settings Tab

- ✅ **Allow task to run on demand**
- ✅ **Run task as soon as possible after a scheduled start is missed**
- ✅ **If task fails, restart every**: `5 minutes`

Click **OK** and save.   