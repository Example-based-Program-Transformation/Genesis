package com.processor.server.service;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class EmployeeService implements IEmployeeService{
	
	public String getEmployeeFname(Employee e) {
		String[] stColl = {"KP", "MR", "KK", "AK"};
		List<String> list = Arrays.asList(stColl);
		List<String> list1 = list.stream().filter(x -> x.startsWith("K")).collect(Collectors.toList());
		System.out.println(list1.size());
		/*if(e == nulll){
			return "";
		}*/
		return e.getFirstName();
	}
	public String getEmployeeCheckStatus(Employee e) {
		String[] stColl = {"KP", "MR", "KK", "AK"};
		List<String> list = Arrays.asList(stColl);
		List<String> list1 = list.stream().filter(x -> x.startsWith("K")).collect(Collectors.toList());
		System.out.println(list1.size());
		return e.toString();
	}
}
