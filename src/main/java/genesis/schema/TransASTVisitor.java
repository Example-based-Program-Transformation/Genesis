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

import java.util.HashMap;
import java.util.Stack;

import genesis.node.MyCtNode;
import spoon.support.reflect.reference.CtLocalVariableReferenceImpl;
import spoon.support.reflect.reference.CtParameterReferenceImpl;

public abstract class TransASTVisitor {
	
	protected Stack<TransASTNode> visitStack;
	
	protected TransASTVisitor() { 
		visitStack = new Stack<TransASTNode>();
	}
	
	public boolean visitCollection(TransASTCollection n) { return true; }
	
	public boolean visitCtEle(TransASTCtEle n) { return true; }
	
	public boolean visitFreeVar(TransASTFreeVar n) { return true; }
	
	public boolean visitTrait(TransASTTrait n) { return true; }
	
	public boolean visitNode(TransASTNode n) { return true; }
	
	public boolean scanNode(TransASTNode n) {
		visitStack.push(n);
		boolean ret = true;
		if (n instanceof TransASTCollection)
			ret = this.scanCollection((TransASTCollection)n);
		else if (n instanceof TransASTCtEle)
			ret = this.scanCtEle((TransASTCtEle) n);
		else if (n instanceof TransASTFreeVar)
			ret = this.scanFreeVar((TransASTFreeVar) n);
		else if (n instanceof TransASTTrait)
			ret = this.scanTrait((TransASTTrait) n);
		else
			assert(false);
		visitStack.pop();
		return ret;
	}
	
	public boolean scanTrait(TransASTTrait n) {
//		System.out.println("scanFreeVar ...");
		return this.visitTrait(n) && this.visitNode(n);
	}
	
	public boolean scanFreeVar(TransASTFreeVar n) {
//		System.out.println("scanFreeVar ...");
		return this.visitFreeVar(n) && this.visitNode(n);
	}
	
	public boolean scanCtEle(TransASTCtEle n) {
		if (!(this.visitCtEle(n) && this.visitNode(n)))
			return false;
		for (String name : n.children.keySet()) {
			if (!this.scanNode(n.children.get(name))) {
				return false;
			}
		}
		return true;
	}
	
	public boolean scanCollection(TransASTCollection n) {
		if (!(this.visitCollection(n) && this.visitNode(n)))
			return false;
		for (TransASTNode child : n.children) {
			if (!this.scanNode(child))
				return false;
		}
		return true;
	}
	
	public static class HJSchemaTreePrinter extends TransASTVisitor {
		Stack<MyCtNode> stack;
		HashMap<Integer, MyCtNode> varBindings;

		HJSchemaTreePrinter(MyCtNode root) {
			this.stack = new Stack<MyCtNode>();
			this.stack.push(root);
			this.varBindings = new HashMap<Integer, MyCtNode>();
		}

		HJSchemaTreePrinter(MyCtNode root, HashMap<Integer, MyCtNode> bindings) {
			this.stack = new Stack<MyCtNode>();
			this.stack.push(root);
			this.varBindings = bindings;
		}

		@Override
		public boolean visitTrait(TransASTTrait n) {
			MyCtNode cur = stack.peek();
			System.out.println("\t\t\t\tHJTreePrinter visitTrait = " + n);
			return true;
		}

		@Override
		public boolean visitFreeVar(TransASTFreeVar n) {
			MyCtNode cur = stack.peek();
//			boolean pass = false;
//			// XXX: So far in genesis we do not separate these two.
//			if (n.nodeSig.isClass(CtLocalVariableReferenceImpl.class, false) && 
//				cur.nodeSig().isClass(CtParameterReferenceImpl.class, false))
//				pass = true;
//			if (n.nodeSig.isClass(CtParameterReferenceImpl.class, false) &&
//				cur.nodeSig().isClass(CtLocalVariableReferenceImpl.class, false))
//				pass = true;
//			if (!n.nodeSig.isSuperOrEqual(cur.nodeSig()) && !pass) 
//				return false;
//			if (!varBindings.containsKey(n.vid))
//				varBindings.put(n.vid, cur);
//			else {
//				if (!cur.treeEquals(varBindings.get(n.vid)))
//					return false;
//			}
			
			System.out.println("\t\t\t\tHJTreePrinter visitFreeVar = " + n);
			return true;
		}

		@Override
		public boolean visitCollection(TransASTCollection n) {
			System.out.println("\t\t HJTreePrinter visitCollection ...");
			MyCtNode cur = stack.peek();
//			if (!cur.isCollection()) 
//				return false;
//			if (!n.nodeSig.isSuperOrEqual(cur.nodeSig())) 
//				return false;
//			if (cur.getNumChildren() != n.children.size()) 
//				return false;
			
			System.out.println("\t\t\t\tHJTreePrinter visitCollection = " + n);
			return true;
		}

		@Override
		public boolean visitCtEle(TransASTCtEle n) {
			System.out.println("\t\t HJTreePrinter visitCtEle ...");
			MyCtNode cur = stack.peek();
//			System.out.println("scanCtEle ... n= " + n);
//			if (cur.isTrait() || cur.isCollection() || cur.isReference()) {
//				System.out.println("\t\t\tvisitCtEle ... return false 1");
//				System.out.println("scanCtEle \t\t\t   :" + cur.isTrait() + " , " +  cur.isCollection() + " , " + cur.isReference());
//				return false;
//			}
//			if (!n.nodeSig.equals(cur.nodeSig())) {
//				System.out.println("\t\t\tvisitCtEle ... return false 2");
//				System.out.println("scanCtEle \t\t\t   :" + n.nodeSig);
//				System.out.println("scanCtEle \t\t\t vs:" + cur.nodeSig());
//				return false;
//			}
//			if (cur.getNumChildren() != n.children.size()) {
//				System.out.println("\t\t\tvisitCtEle ... return false 3");
//				return false;
//			}

			System.out.println("\t\t\t\tHJTreePrinter visitCtEle = " + n);
			return true;
		}

		@Override
		public boolean scanCollection(TransASTCollection n) {
			System.out.println("HJTreePrinter scanCollection ...");
			boolean ret = visitCollection(n) && visitNode(n);
//			if (!ret) 
//				return false;
			
			System.out.println("\t\t\t\tHJTreePrinter scanCollection start = " + n);
			MyCtNode cur = stack.peek();
			try {
				if (cur == null) {
					System.out.println("HJTreePrinter - Let's END EARLY since we get null");
					return false;
				}
			
			} catch (Exception e) {
				System.out.println("HJTreePrinter - Let's END EARLY since we get an exception");
				return false;
			}
			for (int i = 0; i < cur.getNumChildren(); i++) {
				stack.push(cur.getChild(i));
				ret = scanNode(n.children.get(i));
				if (!ret) 
					return false;
				stack.pop();
			}
			
			System.out.println("\t\t\t\tHJTreePrinter scanCollection end = " + n);
			return true;
		}

		@Override
		public boolean scanCtEle(TransASTCtEle n) {
			System.out.println("HJTreePrinter scanCtEle ...");
			boolean ret = visitCtEle(n) && visitNode(n);
			if (!ret) 
				return false;
			MyCtNode cur = stack.peek();
			for (String name : n.children.keySet()) {
				try {
					stack.push(cur.getChild(name));
				
				} catch (Exception e) {
					System.out.println("HJTreePrinter - Let's END EARLY since we get an exception");
					return false;
				}
				System.out.println("HJTreePrinter go into children ... " + name);
				ret = scanNode(n.children.get(name));
				if (!ret) 
					return false;
				stack.pop();
			}
			return true;
		}
	}
}
