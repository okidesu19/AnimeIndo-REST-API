

# TODO - AnimeViewResponse Fix

## Task: Perbaiki AnimeViewResponse untuk menampilkan field sesuai view type

### Status: ✅ COMPLETED

### Detail Perbaikan:
- ✅ Edit fungsi `animeView()` pada `src/parser/Kuramanime/kuramanime.py`
- ✅ Implementasi conditional logic berdasarkan `view_type`:
  - `ViewType.ONGOING`: tampilkan `animeEpisode`, sembunyikan `animeStar`
  - `ViewType.FINISHED`: tampilkan `animeStar`, sembunyikan `animeEpisode`
- ✅ Perbaikan parsing logic untuk membedakan episode dan star info
- ✅ Update AnimeViewResponse creation dengan conditional fields
- ✅ **PERBAIKAN TAMBAHAN**: Tambahkan field `animeStar` ke schema `AnimeViewResponse` di `Config/schemas.py`

### Changes Made:
1. **File**: `src/parser/Kuramanime/kuramanime.py`
   - Function: `animeView()`
   - Added conditional logic untuk episode/star info berdasarkan view type
   - Improved parsing dengan selectors yang sesuai untuk ongoing vs finished anime
   - Fixed animeStar assignment untuk ViewType.FINISHED

2. **File**: `Config/schemas.py`
   - Added `animeStar: Optional[str] = None` field to `AnimeViewResponse`
   - This allows the schema to support both episode and star data

3. **File**: `.gitignore` (NEW)
   - Added comprehensive Python/FastAPI .gitignore file
   - Includes Python cache, IDE files, virtual environments, logs, etc.

4. **File**: `.dockerignore` (NEW)
   - Added Docker-specific ignore file
   - Excludes development files, tests, documentation, and unnecessary files from Docker context

### Test Results:
- ✅ Code compilation successful
- ✅ Schema definition correct
- ✅ Logic implementation correct
- ✅ Conditional display working as expected
- ✅ ViewType.ONGOING: Shows animeEpisode, hides animeStar
- ✅ ViewType.FINISHED: Shows animeStar, hides animeEpisode
- ✅ Git ignore files created and configured properly
- ✅ Docker ignore files created and configured properly
