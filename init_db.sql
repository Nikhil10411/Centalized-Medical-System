-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'medicalAppdb')
BEGIN
    CREATE DATABASE medicalAppdb;
END
GO


