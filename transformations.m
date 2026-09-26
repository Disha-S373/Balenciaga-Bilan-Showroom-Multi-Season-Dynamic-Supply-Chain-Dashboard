// BAL_BILAN — sample Power Query transformations (genericized)

// 1. When loading multiple season files from a folder, exclude non-sheet objects
// (e.g. named ranges, chart objects) that otherwise duplicate rows
let
    Source = Folder.Files("SourceFolderPath"),
    FilteredToSheets = Table.SelectRows(Source, each [Kind] = "Sheet")
in
    FilteredToSheets

// 2. Trim hidden trailing whitespace on status fields — a recurring source of
// "duplicate" categories that were really the same value with an extra space
let
    Source = PreviousStep,
    Trimmed = Table.TransformColumns(
        Source,
        {
            {"FinalStatus", Text.Trim, type text},
            {"FirstFeedbackStatus", Text.Trim, type text}
        }
    )
in
    Trimmed

// 3. Match pre- and post-activity extracts on item code, falling back to a
// "previous code" field when a code change occurred between extracts
let
    Source = PreExtract,
    Matched = Table.AddColumn(
        Source,
        "MatchKey",
        each if [PreviousCode] <> null and [PreviousCode] <> ""
             then [PreviousCode]
             else [ItemCode]
    )
in
    Matched

// 4. Build a season sort key so seasons display in chronological (not alphabetical) order
let
    Source = PreviousStep,
    Sorted = Table.AddColumn(
        Source,
        "SeasonSort",
        each if [Season_Label] = "S1" then 1
             else if [Season_Label] = "S2" then 2
             else if [Season_Label] = "S3" then 3
             else 4
    )
in
    Sorted

// 5. Fall back to a placeholder image when a source row has no image URL,
// so the card-grid HTML visual never renders a broken <img> tag
let
    Source = PreviousStep,
    WithFallback = Table.AddColumn(
        Source,
        "ImageURL_Safe",
        each if [ImageURL] = null or [ImageURL] = ""
             then "https://via.placeholder.com/120x110?text=No+Image"
             else [ImageURL]
    )
in
    WithFallback

// 6. Combine two raw season/period fields from the source system into one
// consistent label used everywhere downstream (model, DAX, visuals)
let
    Source = PreviousStep,
    Combined = Table.AddColumn(
        Source,
        "Season_Label",
        each Text.Combine({[PeriodCode], [YearCode]}, "")
    )
in
    Combined
