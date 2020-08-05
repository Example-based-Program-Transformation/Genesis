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
package genesis;

import java.util.ArrayList;
import java.util.HashSet;

import genesis.node.MyCtNode;
import genesis.node.MyNodeSig;
import spoon.reflect.factory.Factory;

public class SnippetPairParser {
	
	MyCtNode root1, root2;
	MyCtNode oriRoot1, oriRoot2;
	HashSet<MyNodeSig> inside;
	Factory fac1, fac2;
	
	public SnippetPairParser(String path1, String path2) {
		TestSnippetParser s1 = new TestSnippetParser(path1);
		TestSnippetParser s2 = new TestSnippetParser(path2);
		
		root1 = s1.getCtNode();
		root2 = s2.getCtNode();
		oriRoot1 = root1;
		oriRoot2 = root2;
		ArrayList<Object> sargs1 = s1.getStartArgs();
		ArrayList<Object> sargs2 = s2.getStartArgs();
		String sigstr1 = null, sigstr2 = null;
		int cnt1 = 0, cnt2 = 0;
		if ((sargs1.size() != 0) && (sargs1.get(0) instanceof String)) {
			sigstr1 = (String)sargs1.get(0);
			if ((sargs1.size() > 1) && (sargs1.get(1) instanceof Integer))
				cnt1 = (Integer)sargs1.get(1);
			else
				cnt1 = 1;
		}
		if ((sargs2.size() != 0) && (sargs2.get(0) instanceof String)) {
			sigstr2 = (String)sargs2.get(0);
			if ((sargs2.size() > 1) && (sargs2.get(1) instanceof Integer))
				cnt2 = (Integer)sargs2.get(1);
			else
				cnt2 = 1;
		}
		inside = new HashSet<MyNodeSig>();
		while (true) {
			if (cnt1 > 0) {
				MyNodeSig sig = root1.nodeSig();
				while (sig != null) {
					if (sig.toString().startsWith(sigstr1)) {
						cnt1 --;
						break;
					}
					sig = sig.getSuperSig();
				}
			}
			if (cnt2 > 0) {
				MyNodeSig sig = root2.nodeSig();
				while (sig != null) {
					if (sig.toString().startsWith(sigstr2)) {
						cnt2 --;
						break;
					}
					sig = sig.getSuperSig();
				}
			}
			if (cnt1 == 0 && cnt2 == 0) break;
			if (!root1.nodeEquals(root2)) {
				root1 = null;
				root2 = null;
				break;
			}
			int n = root1.getNumChildren();
			for (int i = 0; i < n; i++)
				if (!root1.getChild(i).treeEquals(root2.getChild(i))) {
					inside.add(root1.nodeSig());
					root1 = root1.getChild(i);
					root2 = root2.getChild(i);
					break;
				}
		}
		fac1 = s1.getFactory();
		fac2 = s2.getFactory();
	}
	
	public MyCtNode getTree1() {
		return root1;
	}
	
	public MyCtNode getTree2() {
		return root2;
	}
	
	public MyCtNode getOriTree1() {
		return oriRoot1;
	}
	
	public MyCtNode getOriTree2() {
		return oriRoot2;
	}
	
	public HashSet<MyNodeSig> getInsideSet() {
		return inside;
	}
	
	public Factory getTree1Factory() {
		return fac1;
	}
	
	public Factory getTree2Factory() {
		return fac2;
	}
}
