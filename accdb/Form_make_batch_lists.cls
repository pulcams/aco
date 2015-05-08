VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Form_make_batch_lists"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = True
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Compare Database

Private Sub for_crating_btn_Click()
' output a short list to help with crating the books
On Error GoTo Err_for_crating_Click

    Dim stDocName As String
    Dim batchNo As String
    Dim tableName As String
    Dim pickupDate As String
    
    batchNo = Format(Me.batch_txt.Value, "000")
    pickupDate = Me.pickup_date.Value
    tableName = "for_crating"
    
    DoCmd.SetWarnings False
 
    ' output every record for the given batch, but just a few fields
    SQL = "SELECT [PickList NEW].ITEM_BARCODE AS [Item #], " & _
    "[PickList NEW].ITEM_ENUM AS [Volume #], [PickList NEW].CHRON, " & _
    "[PickList NEW].[Crate No] AS [Crate #], [PickList NEW].TAG_245, " & _
    "[PickList NEW].DISPLAY_CALL_NO AS [Call#], [PickList NEW].batchNo, [PickList NEW].objectNo " & _
    "INTO " & tableName & " " & _
    "FROM [PickList NEW] " & _
    "WHERE [PickList NEW].batchNo =""" & CStr(batchNo) & """ " & _
    "ORDER BY [PickList NEW].[Crate No], [PickList NEW].objectNo;"
 
    If IsObject(CurrentDb.TableDefs(tableName)) Then
        DoCmd.DeleteObject acTable, tableName
    End If
 
    CurrentDb.Execute SQL, dbFailOnError
 
    MsgBox ("created " & tableName & " for printing (right click the table and print).")
    
    DoCmd.SetWarnings True

Exit_for_crating_Click:
    Exit Sub

Err_for_crating_Click:
    MsgBox Err.Description
    Resume Exit_for_crating_Click

End Sub

Private Sub run_query_btn_Click()
' get records from the requested batch into temp table

On Error GoTo Err_run_query_Click

    Dim stDocName As String
    Dim batchNo As String
    Dim tableName As String
    Dim pickupDate As String
    
    batchNo = Format(Me.batch_txt.Value, "000")
    pickupDate = Me.pickup_date.Value
    ' Format(Date, "yyyymmdd")
    tableName = "ACO_princeton_NYU_batch" & batchNo & "_" & pickupDate
    
    DoCmd.SetWarnings False
 
    ' output every record for the given batch
    SQL = "SELECT [PickList NEW].LIB, [PickList NEW].[SYS#],  [PickList NEW].ITEM_BARCODE AS [Item #], " & _
    "[PickList NEW].ITEM_ENUM AS [Volume #], [PickList NEW].CHRON, " & _
    """princeton_aco"" AS CCG_BOOK_ID, [PickList NEW].[Crate No] AS [Crate #], [PickList NEW].Date," & _
    "[PickList NEW].CP, [PickList NEW].TAG_100, [PickList NEW].TAG_240, [PickList NEW].TAG_245," & _
    "[PickList NEW].TAG_260, [PickList NEW].TAG_300, [PickList NEW].TAG_5XX, [PickList NEW].TAG_6XX," & _
    "[PickList NEW].DISPLAY_CALL_NO AS [Call#], [PickList NEW].LOCATION_CODE AS LOC, [PickList NEW].[COMPLETE Y/N]," & _
    "[PickList NEW].NOTES, """" AS [Handling Instructions], [PickList NEW].batchNo, [PickList NEW].objectNo, " & _
    "[PickList NEW].NOS, [PickList NEW].BW, [PickList NEW].Condition, [PickList NEW].CAT_PROB, [PickList NEW].other " & _
    "INTO " & tableName & " " & _
    "FROM [PickList NEW] " & _
    "WHERE [PickList NEW].batchNo =""" & CStr(batchNo) & """ " & _
    "ORDER BY [PickList NEW].[Crate No], [PickList NEW].objectNo;"
 
    CurrentDb.Execute SQL, dbFailOnError
 
    MsgBox ("created " & tableName)
    
    ' add objectNo as autonumber (if staff is not adding objectNo manually)
    'SQL2 = "ALTER TABLE " & tableName & " ADD [objectNo] AUTOINCREMENT(1, 1);"
    'CurrentDb.Execute SQL2, dbFailOnError
    
    DoCmd.SetWarnings True

Exit_run_query_Click:
    Exit Sub

Err_run_query_Click:
    MsgBox Err.Description
    Resume Exit_run_query_Click
    
End Sub

Private Sub export_btn_Click()
' export temp table for processing with py script

On Error GoTo Err_export_btn_Click

    Dim csvpath  As String
    Dim batchNo As String
    Dim tableName As String
    Dim pickupDate As String
    
    pickupDate = Me.pickup_date.Value
    batchNo = Format(Me.batch_txt.Value, "000")
    tableName = "ACO_princeton_NYU_batch" & batchNo & "_" & pickupDate

    csvpath = "\\lib-tsserver\NYU_Arabic_Project\batches\for_peter\" & tableName & ".csv"
    DoCmd.TransferText acExportDelim, , tableName, csvpath, -1, , 65001

MsgBox ("exported to " & csvpath)

' call sub to delete temp table, now that it's been exported
DoCmd.DeleteObject acTable, tableName

Exit_export_btn_Click:
    Exit Sub

Err_export_btn_Click:
    MsgBox Err.Description
    Resume Exit_export_btn_Click
        
End Sub
Private Sub Command8_Click()
On Error GoTo Err_Command8_Click


    Screen.PreviousControl.SetFocus
    DoCmd.FindNext

Exit_Command8_Click:
    Exit Sub

Err_Command8_Click:
    MsgBox Err.Description
    Resume Exit_Command8_Click
    
End Sub
Private Sub Command9_Click()
On Error GoTo Err_Command9_Click


    If Me.Dirty Then Me.Dirty = False
    DoCmd.Quit

Exit_Command9_Click:
    Exit Sub

Err_Command9_Click:
    MsgBox Err.Description
    Resume Exit_Command9_Click
    
End Sub
