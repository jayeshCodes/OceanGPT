import React from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { styled } from "@mui/system";

// Styled DataGrid component
const StyledDataGrid = styled(DataGrid)(({ theme }) => ({
    '& .MuiDataGrid-root': {
      border: 'none',
    },
    '& .MuiDataGrid-cell': {
      borderBottom: `1px solid ${theme.palette.mode === 'dark' ? '#000' : '#000'}`,
    },
    '& .MuiDataGrid-columnHeaders': {
      backgroundColor: '#333',  // Darker color closer to black
      color: '#fff',
      borderBottom: 'none',
    },
    '& .MuiDataGrid-virtualScroller': {
      backgroundColor: '#e0e0e0',  // Gray background for the entire DataGrid
    },
    '& .MuiDataGrid-footerContainer': {
      borderTop: 'none',
      backgroundColor: '#333',
      color: '#fff',
    },
    '& .MuiDataGrid-row': {
      '&:nth-of-type(odd)': {
        backgroundColor: theme.palette.mode === 'dark' ? '#30303' : '#f5f5f5',
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