// Copyright (C) 2016 Fan Long, Peter Amidon, Martin Rianrd and MIT CSAIL 
// Genesis (A successor of Prophet for Java Programs)
// 
// This file is part of Genesis.
// 
// Genesis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 2 of the License, or
// (at your option) any later version.
// 
// Genesis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with Genesis.  If not, see <http://www.gnu.org/licenses/>.
package genesis.schema;

import org.apache.commons.io.FileUtils;
import org.junit.Test;

import genesis.SnippetPairParser;
import genesis.TestSnippetParser;
import genesis.node.MyCtNode;
import genesis.node.MyNodeSig;
import genesis.schema.SchemaAbstractor;
import genesis.schema.SchemaAdapter;
import genesis.schema.TransformSchema;

import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.TreeMap;

import junit.framework.TestCase;
import spoon.Launcher;
import spoon.compiler.*;
import spoon.reflect.cu.CompilationUnit;
import spoon.reflect.declaration.CtPackage;
import spoon.reflect.declaration.CtType;
import spoon.reflect.factory.Factory;
import spoon.reflect.visitor.DefaultJavaPrettyPrinter;
import spoon.reflect.visitor.PrettyPrinter;
import spoon.support.compiler.*;
import spoon.support.gui.SpoonModelTree;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;

public class SchemaAbstractorTest extends TestCase {

	@Test
	public void test() {
		URL folderURL = getClass().getResource("/schema/");
		assertNotNull("Test file not found!", folderURL);
		String[] cases = 
			{"basic", "addguard", "binopchange", "addreturn", "changecond", "addclause", 
			 "removeblock", "removeguard", "addcase", "addelse", "changecall", "addparentheses"};
		String folder = folderURL.getPath();
		int totCnt = 0;
		int passedCnt = 0;
		System.out.println("Schema Abstractor/Adapter unit test:");
		for (String casestr : cases) {
			File onecase = new File(folder + "/" + casestr);
			assertTrue("Unknown structure in resource /schema/", onecase.isDirectory());
			totCnt ++;
			File[] files = onecase.listFiles();
			TreeMap<Integer, File> befores = new TreeMap<Integer, File>();
			TreeMap<Integer, File> afters = new TreeMap<Integer, File>();
			File exp = null;
			for (File f : files) {
				String fname = f.getName();
				if (fname.equals("exp.po"))
					exp = f;
				else if (fname.startsWith("before")) {
					int idx = fname.indexOf(".");
					assertTrue("Wrong file name patten " + fname, idx != -1);
					befores.put(Integer.parseInt(fname.substring(6, idx)), f);
				}
				else if (fname.startsWith("after")) {
					int idx = fname.indexOf(".");
					assertTrue("Wrong file name pattern " + fname, idx != -1);
					afters.put(Integer.parseInt(fname.substring(5, idx)), f);
				}
				else
					fail("Wrong file name pattern " + fname);
			}
			if (befores.size() != afters.size())
				fail("before/after pairs do not match!");
			SchemaAbstractor ab = new SchemaAbstractor();
			ArrayList<MyCtNode> roots1, roots2;
			ArrayList<Factory> factories;
			roots1 = new ArrayList<MyCtNode>();
			roots2 = new ArrayList<MyCtNode>();
			factories = new ArrayList<Factory>();
			for (Integer cid : befores.keySet()) {
				assertTrue("before/after pairs do not match!", afters.containsKey(cid));
				SnippetPairParser parser = new SnippetPairParser(befores.get(cid).getPath(), afters.get(cid).getPath());
				MyCtNode root1 = parser.getTree1();
				MyCtNode root2 = parser.getTree2();
				HashSet<MyNodeSig> inside = parser.getInsideSet();
				if ((root1 == null) || (root2 == null))
					fail("Cannot traverse down to the desired level: " + casestr);
				ab.addMapping(inside, root1, root2);
				roots1.add(root1);
				roots2.add(root2);
				factories.add(parser.getTree1Factory());
			}
			TransformSchema schema = ab.generalize();
			System.out.print("Case " + onecase.getName() + ":\nAbstractor:");
			if (exp == null) {
				System.out.println(Integer.toString(befores.size()) + " snippets\n" + schema.toString());
				String tmpfname = "/tmp/" + onecase.getName() + ".po";
				System.out.println("Going to serialize to " + tmpfname);
				try {
					FileOutputStream fos = new FileOutputStream(tmpfname);
					ObjectOutputStream oos = new ObjectOutputStream(fos);
					oos.writeObject(schema);
					oos.close();
				}
				catch (IOException e) {
					e.printStackTrace();
					System.out.println("IOException during serialization!");
				}
			}
			else {
				TransformSchema expSchema = null;
				try {
					FileInputStream fis = new FileInputStream(exp);
					ObjectInputStream ois = new ObjectInputStream(fis);
					expSchema = (TransformSchema) ois.readObject();
					ois.close();
				}
				catch (Exception e) {
					e.printStackTrace();
					fail("Failed during deserialize from " + exp.getPath());
				}
				if (schema.schemaEquals(expSchema)) {
					System.out.println("OK");
				}
				else {
					System.out.println("DIFF");
					System.out.println("Got:\n" + schema.toString());
					System.out.println("Exp:\n" + expSchema.toString());
					continue;
				}
			}
			
			ArrayList<HashMap<Integer, MyCtNode>> varBindings = ab.getVarBindings();
			System.out.println("Adapter:");
			assertTrue("The size of varbindings should match!", roots1.size() == varBindings.size());
			int n = roots1.size();
			boolean ok = true;
			for (int i = 0; i < n; i++) {
				System.out.print("Snippet " + Integer.toString(i+1) + ":");
				SchemaAdapter sa = new SchemaAdapter(factories.get(i), schema);
				boolean ret = sa.applyTo(roots1.get(i));
				assertTrue("Application of schema failed!", ret);
				HashSet<Integer> postvs = schema.varsInPost();
				for (Integer vid : postvs) {
					assertTrue("Var bindings should contain it!", varBindings.get(i).containsKey(vid));
					sa.setVarBinding(vid, varBindings.get(i).get(vid));
				}
				MyCtNode res = sa.getTransformedTree();
				String str1 = null;
				if (res != null) 
					str1 = res.codeString();
				else
					str1 = "";
				String str2 = roots2.get(i).codeString();
				// Spoon may add parentheses when he does the print 
				if (str1.length() == str2.length() - 2) {
					if (str2.charAt(0) == '(' && str2.charAt(str2.length() - 1) == ')')
						str2 = str2.substring(1, str2.length() - 1);
				}
				if (!str1.equals(str2)) {
					System.out.println("DIFF");
					System.out.println("Got back: " + str1);
					System.out.println("Exp: " + str2);
					ok = false;
				}
				else 
					System.out.println("OK");				
			}
			if (ok) passedCnt ++;
		}
		if (totCnt != passedCnt)
			fail("Some cases produce unexpected output!");
	}

}
