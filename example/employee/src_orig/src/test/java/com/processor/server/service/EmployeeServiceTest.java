package com.processor.server.service;

import static org.junit.Assert.*;

import org.junit.Test;

public class EmployeeServiceTest {

	/*@Test
	public void testCheckEmployeeStatus() {
		EmployeeService result = new EmployeeService();
		assertNotNull(result);
		// add additional test code here
		result.getEmployeeCheckStatus(null);
	}*/
	@Test
	// * com.processor.server.service.EmployeeServiceTest testCheckEmployeeFName 1

	public void testCheckEmployeeFName() {
		EmployeeService result = new EmployeeService();
		assertNotNull(result);
		// add additional test code here
		assertEquals("", result.getEmployeeFname(null));
	}
	@Test
	public void testCheckEmployeeFName_1() {
		EmployeeService result = new EmployeeService();
		Employee emp = new Employee();
		emp.setActive(true);
		emp.setEmpId(1);
		emp.setFirstName("Krishna");
		emp.setLastName("Prasad");
		assertNotNull(result);
		// add additional test code here
		assertEquals("Krishna", result.getEmployeeFname(emp));
	}
}
