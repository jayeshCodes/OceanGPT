import React from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { styled } from "@mui/system";

// Styled DataGrid component
const StyledDataGrid = styled(DataGrid)(({ theme }) => ({
    '& .MuiDataGrid-root': {
      border: 'none',
    },
    '& .MuiDataGrid-cell': {
      borderBottom: `1px solid ${theme.palette.mode === 'dark' ? '#303030' : '#f0f0f0'}`,
    },
    '& .MuiDataGrid-columnHeaders': {
      backgroundColor: '#00cbdd',
      color: '#fff',
      borderBottom: 'none',
    },
    '& .MuiDataGrid-virtualScroller': {
      backgroundColor: theme.palette.mode === 'dark' ? '#424242' : '#fff',
    },
    '& .MuiDataGrid-footerContainer': {
      borderTop: 'none',
      backgroundColor: '#00cbdd',
      color: '#fff',
    },
    '& .MuiDataGrid-row': {
      '&:nth-of-type(odd)': {
        backgroundColor: theme.palette.mode === 'dark' ? '#303030' : '#f5f5f5',
      },
      '&:hover': {
        backgroundColor: theme.palette.mode === 'dark' ? '#3a3a3a' : '#e0e0e0',
      },
    },
    '& .MuiTablePagination-root': {
      color: '#fff',
    },
    '& .MuiTablePagination-selectIcon': {
      color: '#fff',
    },
  }));

export default StyledDataGrid;